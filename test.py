import sys
import unittest
from geetools.tests import image, ee_list, cloud_mask, indices, expressions,\
                           geometry, imagestrip, date
import argparse
# TODO: allow making more than 1 test at a time

tests = {'image': image,
         'list': ee_list,
         'cloud_mask': cloud_mask,
         'indices': indices,
         'expressions': expressions,
         'geometry': geometry,
         'imagestrip': imagestrip,
         'date': date
         }

options = ', '.join(tests.keys())

unittest_args = sys.argv[2:]

def run(module):
    # sys.argv = sys.argv[1:]
    unittest.main(module)


# run(tests[argument])
if __name__ == '__main__':
    # create arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("test",
                        help="run a single test. options: {}".format(options))
    parser.add_argument("unittest_args", nargs='*')
    args = parser.parse_args()

    sys.argv[1:] = args.unittest_args
    argument = args.test
    run(tests[argument])