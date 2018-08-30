import sys
import unittest
from geetools.tests import image, ee_list, cloud_mask, indices, expressions,\
                           geometry, imagestrip

# TODO: allow making more than 1 test at a time

argument = sys.argv[1]


def run(module):
    sys.argv = sys.argv[1:]
    unittest.main(module)


tests = {'image': image,
         'list': ee_list,
         'cloud_mask': cloud_mask,
         'indices': indices,
         'expressions': expressions,
         'geometry': geometry,
         'imagestrip': imagestrip
         }

run(tests[argument])