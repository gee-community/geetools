# coding=utf-8
"""Bit Reader module."""
import ee
import ee.data

import geetools.tools as tools


class BitReader(object):
    """Bit Reader.

    Initializes with parameter `options`, which must be a dictionary with
    the following format:

    keys must be a str with the bits places, example: '0-1' means bit 0
    and bit 1

    values must be a dictionary with the bit value as the key and the category
    (str) as value. Categories must be unique.

    - Encode: given a category/categories return a list of possible values
    - Decode: given a value return a list of categories

    Example:
        MOD09 (http://modis-sr.ltdri.org/guide/MOD09_UserGuide_v1_3.pdf)
        (page 28, state1km, 16 bits):

        ```
        options = {
         '0-1': {0:'clear', 1:'cloud', 2:'mix'},
         '2-2': {1:'shadow'},
         '8-9': {1:'small_cirrus', 2:'average_cirrus', 3:'high_cirrus'}
         }

        reader = BitReader(options, 16)

        print(reader.decode(204))
        ```
        >>['shadow', 'clear']
        ```
        print(reader.match(204, 'cloud')
        ```
        >>False

    """

    @staticmethod
    def getBin(bit, nbits=None, shift=0):
        """from https://stackoverflow.com/questions/699866/python-int-to-binary."""
        pure = bin(bit)[2:]

        if not nbits:
            nbits = len(pure)

        lpure = len(pure)
        admited_shift = nbits - lpure
        if admited_shift < 0:
            mje = (
                "the number of bits must be more than the bits"
                " representation of the number. {} ({}) can't be"
                " represented in {} bits"
            )
            raise ValueError(mje.format(pure, bit, nbits))

        if shift > admited_shift:
            mje = "can't shift {} places for bit {} ({})"
            raise ValueError(mje.format(shift, pure, bit))

        if shift:
            shifted = bin(int(pure, 2) << shift)[2:]
        else:
            shifted = pure
        return shifted.zfill(nbits)

    @staticmethod
    def decodeKey(key):
        """decodes an option's key into a list."""
        if isinstance(key, (str,)):
            bits = key.split("-")

            try:
                ini = int(bits[0])
                if len(bits) == 1:
                    end = ini
                else:
                    end = int(bits[1])
            except Exception:
                mje = (
                    'keys must be with the following format "bit-bit", ' 'example "0-1" (found {})'
                )
                raise ValueError(mje.format(key))

            bits_list = range(ini, end + 1)
            return bits_list
        elif isinstance(key, (int, float)):
            value = int(key)
            return (value, value + 1)

    def __init__(self, options, bit_length=None):
        """TODO missing docstring."""
        self.options = options

        def allBits():
            """get a list of all bits and check consistance."""
            all_values = [x for key in options.keys() for x in self.decodeKey(key)]
            for val in all_values:
                n = all_values.count(val)
                if n > 1:
                    mje = (
                        "bits must not overlap. Example: {'0-1':.., "
                        "'2-3':..} and NOT {'0-1':.., '1-3':..}"
                    )
                    raise ValueError(mje)
            return all_values

        ## Check if categories repeat and create property all_categories
        # TODO: reformat categories if find spaces or uppercases
        all_cat = []
        for key, val in self.options.items():
            for i, cat in val.items():
                if cat in all_cat:
                    msg = 'Classes must be unique, found "{}" twice'
                    raise ValueError(msg.format(cat))
                all_cat.append(cat)

        self.all_categories = all_cat
        ###

        all_values = allBits()

        self.bit_length = (
            len(range(min(all_values), max(all_values) + 1)) if not bit_length else bit_length
        )

        self.max = 2**self.bit_length

        info = {}
        for key, val in options.items():
            bits_list = self.decodeKey(key)
            bit_length_cat = len(bits_list)
            for i, cat in val.items():
                info[cat] = {
                    "bit_length": bit_length_cat,
                    "lshift": bits_list[0],
                    "shifted": i,
                }
        self.info = info

    def encode(self, cat):
        """Given a category, return the encoded value (only)."""
        info = self.info[cat]
        lshift = info["lshift"]
        decoded = info["shifted"]

        shifted = decoded << lshift
        return shifted

    def encodeBand(self, category, mask, name=None):
        """Make an image in which all pixels have the value for the given.

        category.

        :param category: the category to encode
        :type category: str
        :param mask: the mask that indicates which pixels encode
        :type mask: ee.Image
        :param name: name of the resulting band. If None it'll be the same as
            'mask'
        :type name: str

        :return: A one band image
        :rtype: ee.Image
        """
        encoded = self.encode(category)

        if not name:
            name = mask.bandNames().get(0)

        image = tools.image.empty(encoded, [name])
        return image.updateMask(mask)

    def encodeAnd(self, *args):
        """Decodes a combination of the given categories. returns a list of.

        possible values
        .
        """
        first = args[0]
        values_first = self.encodeOne(first)

        def get_match(list1, list2):
            return [val for val in list2 if val in list1]

        result = values_first

        for cat in args[1:]:
            values = self.encodeOne(cat)
            result = get_match(result, values)
        return result

    def encodeOr(self, *args):
        """Decodes a combination of the given categories. returns a list of.

        possible values
        .
        """
        first = args[0]
        values_first = self.encodeOne(first)

        for cat in args[1:]:
            values = self.encodeOne(cat)
            for value in values:
                if value not in values_first:
                    values_first.append(value)

        return values_first

    def encodeNot(self, *args):
        """Given a set of categories return a list of values that DO NOT.

        match with any
        .
        """
        result = []
        match = self.encodeOr(*args)
        for bit in range(self.max):
            if bit not in match:
                result.append(bit)
        return result

    def encodeOne(self, cat):
        """Given a category, return a list of values that match it."""
        info = self.info[cat]
        lshift = info["lshift"]
        length = info["bit_length"]
        decoded = info["shifted"]

        result = []
        for bit in range(self.max):
            move = lshift + length
            rest = bit >> move << move
            norest = bit - rest
            to_compare = norest >> lshift
            if to_compare == decoded:
                result.append(bit)
        return result

    def decode(self, value):
        """given a value return a list with all categories."""
        result = []
        for cat in self.all_categories:
            data = self.info[cat]
            lshift = data["lshift"]
            length = data["bit_length"]
            decoded = data["shifted"]
            move = lshift + length
            rest = value >> move << move
            norest = value - rest
            to_compare = norest >> lshift
            if to_compare == decoded:
                result.append(cat)
        return result

    def decodeImage(self, image, qa_band):
        """Get an Image with one band per category in the Bit Reader.

        :param bit_reader: the bit reader
        :type bit_reader: BitReader
        :param qa_band: name of the band that holds the bit information
        :type qa_band: str
        :return: the image with the decode bands added
        """
        options = ee.Dictionary(self.info)
        categories = ee.List(self.all_categories)

        def eachcat(cat, ini):
            ini = ee.Image(ini)
            qa = ini.select(qa_band)
            # get data for category
            data = ee.Dictionary(options.get(cat))
            lshift = ee.Number(data.get("lshift"))
            length = ee.Number(data.get("bit_length"))
            decoded = ee.Number(data.get("shifted"))
            # move = places to move bits right and left back
            move = lshift.add(length)
            # move bits right and left
            rest = qa.rightShift(move).leftShift(move)
            # subtract the rest
            norest = qa.subtract(rest)
            # right shift to compare with decoded data
            to_compare = norest.rightShift(lshift)  ## Image
            # compare if is equal, return 0 if not equal, 1 if equal
            mask = to_compare.eq(decoded)
            # rename to the name of the category
            qa_mask = mask.select([0], [cat])

            return ini.addBands(qa_mask)

        return ee.Image(categories.iterate(eachcat, image)).select(categories)

    def match(self, value, category):
        """given a value and a category return True if the value includes.

        that category, else False
        .
        """
        encoded = self.decode(value)
        return category in encoded
