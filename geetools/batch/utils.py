"""Missing docstring."""
import os

import ee

GEOMETRY_TYPES = {
    "BBox": ee.geometry.Geometry.BBox,
    "LineString": ee.geometry.Geometry.LineString,
    "LineRing": ee.geometry.Geometry.LinearRing,
    "MultiLineString": ee.geometry.Geometry.MultiLineString,
    "MultiPolygon": ee.geometry.Geometry.MultiPolygon,
    "MultiPoint": ee.geometry.Geometry.MultiPoint,
    "Point": ee.geometry.Geometry.Point,
    "Polygon": ee.geometry.Geometry.Polygon,
    "Rectangle": ee.geometry.Geometry.Rectangle,
    "GeometryCollection": ee.geometry.Geometry,
}


def getProjection(filename, path=None):
    """Get EPSG from a shapefile using pycrs.

    :param filename: an ESRI shapefile (.shp)
    :type filename: str
    """
    try:
        import pycrs
    except ModuleNotFoundError as e:
        print("Install pycrs mode by `pip install pycrs`")
        raise e
    except Exception as e:
        raise e
    import os

    import requests

    if not path:
        path = os.getcwd()

    BASEURL = "http://prj2epsg.org/search.json"
    fname = filename.split(".")[0]
    prjname = "{}.prj".format(fname)
    fpath = os.path.join(path, prjname)
    if not os.path.exists(prjname):
        raise ValueError("{} does not exist".format(fpath))
    crs = pycrs.load.from_file(fpath)
    wkt = crs.to_ogc_wkt()
    params = dict(mode="wkt", terms=wkt)
    response = requests.get(BASEURL, params)
    rjson = response.json()
    return rjson["codes"][0]["code"]


def kmlToGeoJsonDict(kmlfile=None, data=None, encoding=None):
    """Convert a KML file to a GeoJSON dict."""
    import xml.dom.minidom as md

    import kml2geojson
    from fastkml import kml

    k = kml.KML()

    with open(kmlfile) as thefile:
        kmlf = thefile.read()

    # Handle encoding
    if not encoding:
        try:
            import re

            match = re.search('encoding=".+"', kmlf).group()
            encoding = match.split("=")[1][1:-1]
        except Exception:
            encoding = "utf-8"

    kmlf = kmlf.encode(encoding)
    k.from_string(kmlf)
    kmlStr = k.to_string()

    # force encoding
    kmlStr = kmlStr.encode(encoding, errors="ignore").decode()
    root = md.parseString(kmlStr)
    layers = kml2geojson.build_feature_collection(root)
    return layers


def isPoint(pointlist):
    """Verify is a list is a list of points."""
    if len(pointlist) in [2, 3]:
        if isinstance(pointlist[0], (int, float)) and isinstance(pointlist[1], (int, float)):
            return True
        else:
            return False
    else:
        return False


def hasZ(pointlist):
    """Determine if points inside coordinates have Z values."""
    points = pointlist[0]
    first = points[0]
    if len(first) == 3:
        return True
    else:
        return False


def removeZ(coords):
    """Remove Z values from coordinates."""
    newcoords = coords.copy()
    for p in newcoords[0]:
        p.pop(2)
    return newcoords


def downloadFile(url, name, extension, path=None):
    """Download a file from a given url.

    :param url: full url
    :type url: str
    :param name: name for the file (can contain a path)
    :type name: str
    :param extension: extension for the file
    :type extension: str
    :return: the created file (closed)
    :rtype: file
    """
    import requests

    response = requests.get(url, stream=True)
    code = response.status_code

    if path is None:
        path = os.getcwd()

    pathname = os.path.join(path, name)

    while code != 200:
        if code == 400:
            return None
        response = requests.get(url, stream=True)
        code = response.status_code
        size = response.headers.get("content-length", 0)
        if size:
            print("size:", size)

    with open("{}.{}".format(pathname, extension), "wb") as handle:
        for data in response.iter_content():
            handle.write(data)

    return handle


def matchDescription(name, custom=None):
    """Format a name to be accepted as a description.

    The rule is:

    The description must contain only the following characters: a..z, A..Z,
    0..9, ".", ",", ":", ";", "_" or "-". The description must be at most 100
    characters long.
    """
    letters = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]
    numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    upper = [s.capitalize() for s in letters]
    chars = [".", ",", ":", ";", "_", "-"]
    allchars = letters + upper + chars + numbers

    replacements = [
        [" ", [" "]],
        ["-", ["/"]],
        [".", ["?", "!", "¿", "*"]],
        [":", ["(", ")", "[", "]", "{", "}"]],
        ["a", ["á", "ä", "à", "æ"]],
        ["e", ["é", "ë", "è"]],
        ["i", ["í", "ï", "ì"]],
        ["o", ["ó", "ö", "ò", "ø"]],
        ["u", ["ú", "ü", "ù"]],
        ["c", ["¢", "ç"]],
        ["n", ["ñ"]],
    ]

    replacementupper = []
    for r in replacements:
        row = []
        row.append(r[0].capitalize())
        row2 = []
        for alt in r[1]:
            row2.append(alt.capitalize())
        row.append(row2)
        replacementupper.append(row)

    replacements_dict = dict()
    for replacement in replacements + replacementupper:
        letter = replacement[0]
        repl = replacement[1]
        for char in repl:
            replacements_dict[char] = letter

    # user custom mapping
    if custom:
        replacements_dict.update(custom)

    description = ""
    for letter in name:
        if letter not in allchars:
            if letter in replacements_dict:
                description += replacements_dict[letter]
            else:
                description += ""
        else:
            description += letter

    return description[0:100]
