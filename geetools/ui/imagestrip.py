# coding=utf-8

""" Creation of strip of images """

from __future__ import print_function
from .. import batch
from PIL import Image as ImPIL
from PIL import ImageDraw, ImageFont
import os.path
import ee
import logging
from copy import deepcopy
from ..tools import geometry
from .. import utils
import requests
from io import BytesIO
import os
import hashlib


def split(alist, split):
    """ split a list into 'split' items """
    newlist = []
    accum = []
    for i, element in enumerate(alist):
        accum.append(element)
        if (len(accum) == split) or (i == len(alist)-1):
            newlist.append(accum)
            accum = []

    return newlist


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


class Block(object):
    def __init__(self, position=(0, 0), background_color=None):
        self.position = position
        self.background_color = background_color or "#00000000" # transparent

    def image(self):
        """ Overwrite this method """
        im = ImPIL.new("RGBA", self.size(), self.background_color())
        return im

    def height(self):
        """ Overwrite this method """
        return 0

    def width(self):
        """ Overwrite this method """
        return 0

    def size(self):
        return (self.width(), self.height())

    def topleft(self):
        return self.position

    def topright(self):
        x = self.position[0] + self.width()
        return (x, self.position[1])

    def bottomleft(self):
        y = self.position[1] + self.height()
        return (self.position[0], y)

    def bottomright(self):
        x = self.position[0] + self.width()
        y = self.position[1] + self.height()
        return (x, y)


class TextBlock(Block):
    def __init__(self, text, font=None, color='white', font_size=12,
                 y_space=10, **kwargs):
        super(TextBlock, self).__init__(**kwargs)
        self.text = text
        self.color = color
        self.font_size = font_size
        self.y_space = y_space
        if not isinstance(font, ImageFont.FreeTypeFont):
            if font is None:
                self.font = ImageFont.truetype("DejaVuSerif.ttf", self.font_size)
            else:
                self.font = ImageFont.truetype(font, self.font_size)
        else:
            self.font = font

    def image(self):
        """ Return the PIL image """
        image = ImPIL.new("RGBA", self.size(), self.background_color)
        draw = ImageDraw.Draw(image)
        draw.text(self.position, self.text,
                  font=self.font, fill=self.color)
        return image

    def height(self):
        """ Calculate height for a multiline text """
        alist = self.text.split("\n")
        alt = 0
        for line in alist:
            alt += self.font.getsize(line)[1]
        return alt + self.y_space + self.position[1]

    def width(self):
        """ Calculate height for a multiline text """
        alist = self.text.split("\n")
        widths = []
        for line in alist:
            w = self.font.getsize(line)[0]
            widths.append(w)
        return max(widths) + self.position[0]

    def draw(self, image, position=(0,0)):
        """ Draw the text image into another PIL image """
        im = self.image()
        newi = image.copy()
        newi.paste(im, position, im)
        return newi


class ImageBlock(Block):
    def __init__(self, source, **kwargs):
        """ Image Block for PIL images """
        super(ImageBlock, self).__init__(**kwargs)
        self.source = source

    def height(self):
        return self.source.size[1] + self.position[1]

    def width(self):
        return self.source.size[0] + self.position[0]

    def image(self):
        im = ImPIL.new("RGBA", self.size(), self.background_color)
        im.paste(self.source, self.position)
        return im


class EeImageBlock(Block):
    def __init__(self, source, visParams=None, region=None,
                 download=False, check=True, path=None, name=None,
                 extension=None, dimensions=(500, 500), **kwargs):
        """ Image Block for Earth Engine images """
        super(EeImageBlock, self).__init__(**kwargs)
        self.source = ee.Image(source)
        self.visParams = visParams or dict(min=0, max=1)
        self.dimensions = dimensions
        self.download = download
        self.extension = extension or 'png'
        self.check = check
        self.visual = self.source.visualize(**self.visParams)
        self.name = name

        if region:
            self.region = geometry.getRegion(region, True)
        else:
            self.region = geometry.getRegion(self.source, True)

        if download:
            self.path = path or os.getcwd()
            h = hashlib.sha256()
            tohash = self.visual.serialize()+str(self.dimensions)+str(self.region)
            h.update(tohash.encode('utf-8'))
            namehex = h.hexdigest()
            if not name:
                self.name = namehex
            else:
                self.name = '{}_{}'.format(self.name, namehex)
        else:
            self.path = path

        self._pil_image = None
        self._url = None

    @property
    def pil_image(self):
        if not self._pil_image:
            if not self.download:
                raw = requests.get(self.url)
                self._pil_image = ImPIL.open(BytesIO(raw.content))
            else:
                if not os.path.exists(self.path):
                    os.mkdir(self.path)
                filename = '{}.{}'.format(self.name, self.extension)
                fullpath = os.path.join(self.path, filename)
                exist = os.path.isfile(fullpath)
                if self.check and exist:
                    self._pil_image = ImPIL.open(fullpath)
                else:
                    file = batch.utils.downloadFile(self.url, self.name,
                                                    self.extension, self.path)
                    self._pil_image = ImPIL.open(file.name)

        return self._pil_image

    @staticmethod
    def format_dimensions(dimensions):
        x = dimensions[0]
        y = dimensions[1]
        if x and y: return "x".join([str(d) for d in dimensions])
        elif x: return str(x)
        else: return str(y)

    @property
    def url(self):
        if not self._url:
            vis = utils.formatVisParams(self.visParams)
            vis.update({'format':self.extension, 'region':self.region,
                        'dimensions':self.format_dimensions(self.dimensions)})
            url = self.source.getThumbURL(vis)
            self._url = url

        return self._url

    def height(self):
        return self.pil_image.size[1] + self.position[1]

    def width(self):
        return self.pil_image.size[0] + self.position[0]

    def image(self):
        im = ImPIL.new("RGBA", self.size(), self.background_color)
        im.paste(self.pil_image, self.position)
        return im


class GridBlock(Block):
    def __init__(self, blocklist, x_space=10, y_space=10, **kwargs):
        """ """
        super(GridBlock, self).__init__(**kwargs)
        self.blocklist = self._format_blocklist(blocklist)
        self.x_space = x_space
        self.y_space = y_space

    @staticmethod
    def _format_blocklist(blocklist):
        rows = len(blocklist)
        cols = 0
        for l in blocklist:
            length = len(l)
            cols = length if length > cols else cols

        row = [None]*cols
        empty = []
        for i in range(rows):
            empty.append(deepcopy(row))

        for row_n, r in enumerate(blocklist):
            for col_n, block in enumerate(r):
                empty[row_n][col_n] = block

        return empty

    def get(self, x, y):
        """ Get a block given it's coordinates on the grid """
        return self.blocklist[x][y]

    def row_height(self, row):
        r = self.blocklist[row]
        h = 0
        for im in r:
            imh = im.height() if im else 0
            # update h if image height is bigger
            h = imh if imh > h else h
        return h

    def height(self):
        heightlist = []
        for l in self.blocklist:
            h = 0
            for block in l:
                bh = block.height() if block else 0
                # update h if image height is bigger
                h = bh if bh > h else h
            heightlist.append(h)
        return sum(heightlist) + ((len(heightlist)-1) * self.y_space)

    def width(self):
        widthlist = []
        for l in self.blocklist:
            w = 0
            for block in l:
                bw = block.width() if block else 0
                w += bw
            w = w + ((len(l)-1) * self.x_space)
            widthlist.append(w)
        return max(widthlist)

    def image(self):
        im = ImPIL.new("RGBA", self.size(), self.background_color)
        nextpos = (0, 0)
        for rown, blist in enumerate(self.blocklist):
            for block in blist:
                if block:
                    i = block.image()
                    im.paste(i, nextpos)
                    nextwidth = nextpos[0] + block.width() + self.x_space
                    nextpos = (nextwidth, nextpos[1])
            nextpos = (0, nextpos[1] + self.row_height(rown) + self.y_space)
        return im


class ImageStrip(object):
    """ Create an image strip """
    def __init__(self, extension="png", **kwargs):
        """
        :Opcionals:

        :param extension: Extension. Default: png
        :type extension: str
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
        """
        self.extension = extension

        self.body_size = kwargs.get("body_size", 20)
        self.title_size = kwargs.get("title_size", 30)
        self.description_size = kwargs.get("title_size", 15)
        self.font = kwargs.get("font", "DejaVuSerif.ttf")
        self.background_color = kwargs.get("background_color", "white")
        self.title_color = kwargs.get("title_color", "black")
        self.body_color = kwargs.get("body_color", "black")
        self.general_width = kwargs.get("general_width", 0)
        self.general_height = kwargs.get("general_height", 0)
        self.y_space = kwargs.get("y_space", 10)
        self.x_space = kwargs.get("x_space", 15)

        self.body_font = ImageFont.truetype(self.font, self.body_size)
        self.title_font = ImageFont.truetype(self.font, self.title_size)
        self.description_font = ImageFont.truetype(self.font, self.description_size)

    @staticmethod
    def unpack(doublelist):
        return [y for x in doublelist for y in x]

    def fromList(self, image_list, name=None, name_list=None, vis_params=None,
                 region=None, split_at=4, image_size=(500, 500),
                 description_list=None, images_folder=None, check=True,
                 download_images=False, save=True, folder=None):
        """ Download every image and create the strip

        :param image_list: Satellite Images (not PIL!!!!!!)
        :type image_list: list of ee.Image
        :param name_list: Names for the images. Must match imlist
        :type name_list: list of str
        :param description_list: list of descriptions for every image. Optional
        :type description_list: list of str
        :param vis_params: Visualization parameters
        :type vis_params: dict
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
        if isinstance(image_list, ee.List):
            image_list = listEE2list(image_list, 'Image')

        if region:
            region = geometry.getRegion(region, True)

        description_list = description_list or [None]*len(image_list)
        name_list = name_list or [None]*len(image_list)

        ilist = split(image_list, split_at)
        nlist = split(name_list, split_at)
        dlist = split(description_list, split_at)

        final_list = []

        for imgs, names, descs in zip(ilist, nlist, dlist):
            row_list = []
            for image, iname, desc in zip(imgs, names, descs):

                if download_images:
                    if images_folder:
                        path = os.path.join(os.getcwd(), images_folder)
                    else:
                        if name:
                            path = os.path.join(os.getcwd(), name)
                        else:
                            path = os.getcwd()
                    if not os.path.exists(path):
                        os.mkdir(path)
                else:
                    path = None

                imgblock = EeImageBlock(image, vis_params, region, check=check, name=iname,
                                        extension=self.extension, dimensions=image_size,
                                        download=download_images, path=path)
                blocklist = [[imgblock]]

                # IMAGE NAME BLOCK
                if iname:
                    textblock = TextBlock(iname,
                                          color=self.body_color,
                                          background_color=self.background_color,
                                          font=self.body_font,
                                          )

                    blocklist.append([textblock])

                # DESCRIPTION
                if desc:
                    descblock = TextBlock(desc,
                                          color=self.body_color,
                                          background_color=self.background_color,
                                          font=self.description_font,
                                          )
                    blocklist.append([descblock])

                # FINAL CELL BLOCK
                block = GridBlock(blocklist,
                                  background_color=self.background_color,
                                  x_space=self.x_space,
                                  y_space=self.y_space
                                  )

                row_list.append(block)
            final_list.append(row_list)

        # TITLE
        if name:
            title_tb = TextBlock(name,
                                 color=self.title_color,
                                 background_color=self.background_color,
                                 font=self.font,
                                 font_size=self.title_size
                                 )

            final_list.insert(0, [title_tb])

        grid = GridBlock(final_list,
                         background_color=self.background_color,
                         x_space=self.x_space,
                         y_space=self.y_space
                         )

        i = grid.image()

        if save:
            stripname = '{}.{}'.format(name, self.extension)
            local = os.getcwd()
            if not folder:
                path = os.path.join(local, stripname)
            else:
                path = os.path.join(local, folder, stripname)

            i.save(path)

        return i

    def fromCollection(self, collection, title=None, name='{id}',
                       description=None, date_pattern=None, **kwargs):
        """ Create an image strip from a collection """
        collist = collection.toList(collection.size())
        # FILL NAME LIST
        namelist = collist.map(lambda img: utils.makeName(
            ee.Image(img), name, date_pattern))
        namelist = namelist.getInfo()
        params = dict(name=title, name_list=namelist)
        # FILL DESCRIPTION
        if description:
            desclist = collist.map(lambda img: utils.makeName(
                ee.Image(img), description, date_pattern))
            desclist = desclist.getInfo()
            params['description_list'] = desclist

        kwargs.update(params)
        return self.fromList(collist, **kwargs)