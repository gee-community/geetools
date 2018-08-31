# coding=utf-8
''' Creation of strip of images '''

from __future__ import print_function
from .. import batch
from PIL import Image as ImPIL
from PIL import ImageDraw, ImageFont
import os.path
import ee
import logging

def listEE2list(listEE, type='Image'):
    relation = {'Image': ee.Image,
                'Number': ee.Number,
                'String': ee.String,
                'Feature': ee.Feature}
    size = listEE.size().getInfo()
    newlist = []
    for el in range(size):
        newlist.append(relation[type](listEE.get(el)))

    return newlist

class ImageStrip(object):
    ''' Create an image strip '''
    def __init__(self, name, ext="png", description="", **kwargs):
        '''
        :param name: File name
        :type name: str

        :Opcionals:

        :param ext: Extention. Default: png
        :type ext: str
        :param body_size: Body size. Defaults to 18
        :type body_size: int
        :param title_size: Title's font size. Defaults to 30
        :type title_size: int
        :param font: Font for all texts. defaults to "DejaVuSerif.ttf"
        :type font: str
        :param background_color: Background color. defaults to "white"
        :type background_color: str
        :param title_color: Title's font color. defaults to "black"
        :type title_color: str
        :param body_color: Body's text color. defaults to "red"
        :type body_color:  str
        :param general_width: defaults to 0
        :type general_width: int
        :param general_height: defaults to 0
        :type general_height: int
        :param y_space: Space between lines or rows. defaults to 10
        :type y_space: int
        :param x_space: Space between columns. defaults to 15
        :type x_space: int
        :param description: Description that will go beneath the title
        :type description: str
        '''
        self.name = name
        self.ext = ext
        self.description = description

        self.body_size = kwargs.get("body_size", 18)
        self.title_size = kwargs.get("title_size", 30)
        self.font = kwargs.get("font", "DejaVuSerif.ttf")
        self.background_color = kwargs.get("background_color", "white")
        self.title_color = kwargs.get("title_color", "black")
        self.body_color = kwargs.get("body_color", "red")
        self.general_width = kwargs.get("general_width", 0)
        self.general_height = kwargs.get("general_height", 0)
        self.y_space = kwargs.get("y_space", 10)
        self.x_space = kwargs.get("x_space", 15)

    @staticmethod
    def unpack(doublelist):
        return [y for x in doublelist for y in x]

    def create(self, imlist, namelist, desclist=None):
        """ Main method to create the actual strip
        
        :param imlist: PIL images, ej: [[img1, img2],[img3, img4]]
        :type imlist: list of lists
        :param namelist: Names for the images. Must match imlist size
        :type namelist: list of lists
        :param desclist: Descriptions for the images. Must match imlist size
        :type desclist: list of lists
        :return:
        :rtype:
        """

        # SANITY CHECK
        err1 = "dimension of imlist must match dimension of namelist"
        err2 = "dimension of nested lists must be equal"

        if len(imlist) != len(namelist):
            raise ValueError(err1)
        elif [len(l) for l in imlist] != [len(l) for l in namelist]:
            raise ValueError(err2)

        if desclist is not None:
            if len(desclist) != len(imlist):
                raise ValueError(err1)
            elif [len(l) for l in imlist] != [len(l) for l in desclist]:
                raise ValueError(err2)

        def line_height(text, font):
            """ Calculate height for a multiline text
            
            :param text: multiline text
            :type text: str
            :param font: utilized font
            :type font: ImageFont
            :return: text height
            :rtype: float
            """
            lista = text.split("\n")
            alt = 0
            for linea in lista:
                alt += font.getsize(linea)[1]
            return alt + self.y_space

        # FUENTES
        font = ImageFont.truetype(self.font, self.body_size)
        fontit = ImageFont.truetype(self.font, self.title_size)
        font_desc = ImageFont.truetype(self.font, self.title_size - 4)

        # TITULO
        title = self.name
        title_height = line_height(title, fontit)
        
        # DIMENSIONES DESCRIPCION
        description = self.description.replace("_", "\n")
        desc_height = line_height(description, font_desc)
        desc_width = font_desc.getsize(description)[0]

        # ALTURA NOMBRES
        if desclist:
            all_names = [n.replace("_", "\n") for n in self.unpack(desclist)]
        else:
            all_names = [n.replace("_", "\n") for n in self.unpack(namelist)]

        all_height = [line_height(t, font) for t in all_names]
        name_height = max(*all_height) #+ 2
        # print alturatodos, alturanombres

        # CALCULO EL ANCHO DE LA PLANTILLA
        imgs_width = [[ii.size[0] + self.x_space for ii in i] for i in imlist]
        imgs_width_sum = [sum(i) for i in imgs_width]

        # CALCULO EL MAXIMO ANCHO DE LA LISTA DE ANCHOS
        max_width = max(imgs_width_sum)
        strip_width = int(max_width)

        # CALCULO EL ALTO MAX

        # POR AHORA LO CALCULA CON EL ALTO DE LA 1ER COLUMNA
        # PERO SE PODRIA CALCULAR CUAL ES LA IMG MAS ALTA Y CUAL
        # ES EL TITULO MAS ALTO, Y COMBINAR AMBOS...

        # Tener en cuenta que listaimgs es una lista de listas [[i1,i2], [i3,i4]]

        # print "calculando general_height de la plantilla..."

        imgs_height = [[ii.size[1] for ii in i] for i in imlist]
        max_imgs_height = [max(*i) + name_height + self.y_space for i in imgs_height]
        max_height = sum(max_imgs_height)

        strip_height = int(sum((title_height, desc_height, max_height,
                                    self.y_space * 3)))

        strip = ImPIL.new("RGB", (strip_width, strip_height),
                              self.background_color)

        draw = ImageDraw.Draw(strip)

        # DIBUJA LOS ELEMENTOS DENTRO DE LA PLANTILLA

        # COORD INICIALES
        x = 0
        y = 0

        # DIBUJA EL TITULO
        draw.text((x, y), title, font=fontit, fill=self.title_color)

        # DIBUJA LA DESCRIPCION
        y += title_height + self.y_space # aumento y
        # print "y de la descripcion:", y
        draw.text((x, y), description, font=font_desc, fill=self.title_color)

        # DIBUJA LAS FILAS

        # logging.debug(("altura de la descripcion (calculada):", desc_height))
        # logging.debug(("altura de la desc", font_desc.getsize(description)[1]))
        y += desc_height + self.y_space # aumento y

        # DIBUJA LAS FILAS Y COLUMNAS

        if desclist:
            namelist = desclist

        for i, n, alto in zip(imlist, namelist, max_imgs_height):
            # RESETEO LA POSICION HORIZONTAL
            xn = x # hago esto porque en cada iteracion aumento solo xn y desp vuelvo a x
            for image, name in zip(i, n):
                # LA COLUMNA ES: (imagen, name, anchocolumna)
                # print image, name

                ancho_i, alto_i = image.size

                # DIBUJO imagen
                strip.paste(image, (xn, y))

                # aumento y para pegar el texto
                _y = y + alto_i + self.y_space

                # DIBUJO name
                draw.text((xn, _y),
                          name.replace("_", "\n"),
                          font=font,
                          fill=self.body_color)

                # AUMENTO y
                xn += ancho_i + self.x_space

            # AUMENTO x
            y += alto

        strip.save(self.name + "." + self.ext)
        strip.show()

        return strip

    def from_list(self, imlist, namelist, viz_bands, min, max, region,
                  folder, check=True, desclist=None, **kwargs):
        """ Download every image and create the strip

        :param imlist: Satellite Images (not PIL!!!!!!)
        :type imlist: list of ee.Image
        :param namelist: Names for the images. Must match imlist
        :type namelist: list of str
        :param desclist: list of descriptions for every image. Optional
        :type desclist: list of str
        :param viz_bands: Visualization bands. ej: ["NIR","SWIR","RED"]
        :type viz_bands: list of str
        :param min: min value for visualization
        :type min: int
        :param max: max value for visualization
        :type max: int
        :param region: coordinate list. Optional
        :type region: list
        :param folder: folder to downlaod files. Do not use '/' at the end
        :type folder: str
        :param check: Check if file exists, and if it does, omits the downlaod
        :type check: bool
        :param draw_polygons: Polygons to draw over the image. Must be a list of list of
            coordinates. Optional
        :type draw_polygons: list of list
        :param draw_lines: Lines to draw over the image
        :type draw_lines: list of list
        :param draw_points: Points to draw over the image
        :type draw_points: list of list
        :param general_width: Images width
        :type general_width: int

        :return: A file with the name passed to StripImage() in the folder
            passed to the method. Opens the generated file
        """

        if isinstance(imlist, ee.List):
            imlist = listEE2list(imlist, 'Image')

        region = ee.Geometry.Polygon(region).bounds().getInfo()["coordinates"]

        # TODO: modificar este metodo para que se pueda pasar listas de listas
        general_width = kwargs.get("general_width", 500)

        draw_polygons = kwargs.get("draw_polygons", None)
        draw_lines = kwargs.get("draw_lines", None)
        draw_points = kwargs.get("draw_points", None)

        # desclist = kwargs.get("desclist", None)

        list_of_lists = []

        # logging.debug(("verificar archivo?", check))

        # for i in range(0, len(imlist)):
        for img_list, nom_list in zip(imlist, namelist):
            pil_img_list = []
            for image, name in zip(img_list, nom_list):
                # name = namelist[i]
                # exist = os.path.exists(folder+"/"+name)
                # path = "{0}/{1}.{2}".format(folder, name, self.ext)

                # CHECK CARPETA
                abscarp = os.path.abspath(folder)
                if not os.path.exists(abscarp):
                    os.mkdir(abscarp)

                path = "{}/{}".format(folder, name)
                fullpath = os.path.abspath(path)+"."+self.ext
                exist = os.path.isfile(fullpath)

                logging.debug(("existe {}?".format(fullpath), exist))

                if check and exist:
                    im = ImPIL.open(fullpath)
                else:
                    img = ee.Image(image)
                    urlviz = img.visualize(bands=viz_bands, min=min, max=max,
                                           forceRgbOutput=True)

                    url = urlviz.getThumbURL({"region": region,
                                              "format": self.ext,
                                              "dimensions": general_width})

                    # archivo = funciones.downloadFile3(url, folder+"/"+name, self.ext)
                    file = batch.downloadFile(url, path, self.ext)

                    im = ImPIL.open(file.name)
                    # listaimPIL.append(im)

                dr = ImageDraw.Draw(im)

                general_width, general_height = im.size
                # print "general_width:", general_width, "general_height:", general_height

                # nivel de 'anidado' (nested)
                def nested_level(l):
                    n = 0
                    while type(l[0]) is list:
                        n += 1
                        l = l[0]
                    return n

                region = region[0] if nested_level(region) == 2 else region
                region = region[:-1] if len(region) == 5 else region

                p0 = region[0]
                p1 = region[1]
                p3 = region[3]
                distX = abs(p0[0]-p1[0])
                distY = abs(p0[1]-p3[1])

                # FACTORES DE ESCALADO
                width_ratio = float(general_width)/float(distX)
                height_ratio = float(general_height)/float(distY)

                if draw_polygons:
                    for pol in draw_polygons:
                        pol = [tuple(p) for p in pol]

                        newpol = [(abs(x-p0[0])*width_ratio, abs(y-p0[1])*height_ratio) for x, y in pol]

                        # logging.debug("nuevas coords {}".format(newpol))

                        #print "\n\n", pol, "\n\n"
                        dr.polygon(newpol, outline="red")

                pil_img_list.append(im)
            list_of_lists.append(pil_img_list)

        if desclist:
            return self.create(list_of_lists, namelist, desclist)
        else:
            return self.create(list_of_lists, namelist)

    def from_collection(self, collections, viz_param=None, region=None,
                        name=None, folder=None, properties=None,
                        drawRegion=False, zoom=0, description="", **kwargs):
        ''' Create an image strip from a given ee.ImageCollection or ee.List

        :param collections: contains the images (ee.Image)
        :type collections: list of ee.ImageCollection or ee.List
        :param viz_param: visualization parameters. If None will use data of
            the first 3 bands.
        :type viz_param: dict
        :param region: region from where to create the image strip. If None,
            the region of the first image is used
        :type region: list of list
        :param name: name for the folder. If None the name of the
            collection will be used
        :type name: str
        :param folder: folder to save the file. If None, the name of the
            collection will be used
        :type folder: str
        :param properties: properties to add as a description of every image
        :type properties: list
        :param drawRegion: draw a polygon in the given region
        :type drawRegion: bool
        :param zoom: doesn't match EE zoom, this strats from 0 (no zoom).
        :type zoom: int
        :param description: Paragraph that serves as a decription of the image
            strip
        :type description: str
        :param kwargs: other parameters passed to the creation of the
            ImageStrip object.
        :type kwargs: dict
        :return: A file with the name passed to StripImage() in the folder
            passed to the method. Opens the generated file
        '''
        # SANITY CHECK
        coltypes_imcol = [isinstance(col, ee.ImageCollection) for col in collections]
        coltypes_imlist = [isinstance(col, ee.List) for col in collections]
        if not min(coltypes_imcol) and not min(coltypes_imlist):
            raise ValueError("'collection' parameter must be a list of " \
                "ee.ImageCollection or a list of ee.List containing ee.Image")

        if folder is None:
            folder = name

        # TOMA DATOS DE LA PRIMER IMAGEN POR SI NO SE ESPECIFICA LA REGION O LOS
        # PARAMETROS PARA LA VISUALIZACION
        first = ee.Image(collections[0].first())
        first_info = first.getInfo()

        # OBTENGO LA REGION, DE ESTE MODO SE PUEDE ESPECIFICAR UN AREA MAS CHICA
        if not region:
            region = first.geometry().bounds().getInfo()["coordinates"]

        original_region = region

        maxError = kwargs.get("maxError", 10)
        if zoom > 0:
            pol = ee.Geometry.Polygon(region)
            center = pol.centroid()
            b = center.buffer(zoom*100, maxError).bounds()
            region = b.getInfo()["coordinates"]

        if viz_param:
            bands = viz_param.get("bands")
            minV = viz_param.get("min")
            maxV = viz_param.get("max")
        else:
            bandtype = first_info["bands"][0]["data_type"]["precision"]
            bandmax = first_info["bands"][0]["data_type"]["max"]
            b1 = first_info["bands"][0]["id"]
            b2 = first_info["bands"][1]["id"]
            b3 = first_info["bands"][2]["id"]
            bands = [b1, b2, b3]
            minV = 0
            if bandtype == "int" and bandmax > 255:
                maxV = 5000
            elif bandtype == "float":
                maxV = 0.5
            elif bandtype == "int" and bandmax == 255:
                maxV = 125
            else:
                maxV = 0.5

        zoom_str = "z"+str(zoom)
        region_str = "with_region" if drawRegion else "without_region"

        name += "_" + "_".join((zoom_str, region_str))

        pl = ImageStrip(name, description=description)

        nested_imgs = []
        nested_names = []
        nested_desc = []

        for col in collections:
            # TRANSFORMO LA COLECCION EN UNA LISTA
            lista = col.toList(5000)
            listaPy = []
            names = []
            descriptions = [] # description para cada imagen
            size = lista.size().getInfo()
            # colID = funciones.execli(col.getInfo)()["id"].split("/")[-1]

            for i in range(0, size):
                img = ee.Image(lista.get(i))
                listaPy.append(img)
                date = img.date().format().getInfo()
                imID = img.id().getInfo()
                propname = ""
                if properties:
                    for prop in properties:
                        value = img.get(prop).getInfo()
                        value = str(value) if value else "no {} property".format(value)
                        propname += "{}: {}_".format(prop, value)

                # desc = "{fecha}".format(id=imID, fecha=date)
                desc = "ID: {imID}_date: {date}_{propname}".format(**locals())
                # nn = "_".join((colID, str(date), zoom_str, buff_str))
                nn = "_".join((imID, str(date), zoom_str))

                names.append(nn)
                descriptions.append(desc)

            # logging.debug(("descripciones", descripciones))
            # logging.debug(("nombres", nombres))

            nested_imgs.append(listaPy)
            nested_names.append(names)
            nested_desc.append(descriptions)

        arguments = dict(
            imlist=nested_imgs,
            namelist=nested_names,
            desclist=nested_desc,
            viz_bands=bands,
            min=minV,
            max=maxV,
            region=region,
            folder=folder,
            check=True)

        if drawRegion:
            arguments["draw_polygons"] = (original_region)

        # print arguments["draw_polygons"]

        i = pl.from_list(**arguments)

        return i