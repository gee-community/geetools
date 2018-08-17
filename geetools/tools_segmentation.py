# coding=utf-8
""" Tools for Earth Engine Segmentation algorithms """

import ee
import ee.data
if not ee.data._initialized: ee.Initialize()


class SNIC(object):
    """ tools for SNIC segmentation.

    Superpixel clustering based on SNIC (Simple Non-Iterative Clustering).
    Outputs a band of cluster IDs and the per-cluster averages for each of the
    input bands. If the 'seeds' image isn't provided as input, the output will
    include a 'seeds' band containing the generated seed locations. See:
    Achanta, Radhakrishna and Susstrunk, Sabine, 'Superpixels and Polygons
    using Simple Non-Iterative Clustering', CVPR, 2017."""

    def __init__(self, image, **kwargs):
        self.image = image
        self.original = ee.Algorithms.Image.Segmentation.SNIC(image, **kwargs)

    def compute(self, scale=None, compactness=0):
        """ Compute SNIC at the specified scale

        :param scale: scale to compute the segmentation. If None, uses image
            first band scale
        :type scale: int
        :param compactness: same as original algorithms, but defaults to 0
        :type compactness: int
        :rtype: ee.Image
        """

        scale = scale if scale else self.image.select([0]).projection()\
                                                          .nominalScale()

        projection = self.image.projection().atScale(scale)

        return self.original.reproject(projection)

    def extract_features(self, func):
        """ Extract features in each cluster given a function """
        pass