:html_theme.sidebar_secondary.remove:


geetools
========

.. toctree::
   :hidden:

   usage/index
   example/index
   autoapi/index
   Changelogs <https://github.com/gee-community/geetools/releases>
   earth-engine API <https://developers.google.com/earth-engine/apidocs>

Overview
--------

.. image:: _static/logo.png
    :width: 20%
    :align: right
    :class: dark-light

`Google Earth Engine <https://earthengine.google.com/>`__ is a cloud-based service for geospatial processing of vector and raster data. The Earth Engine platform has a `JavaScript and a Python API <https://developers.google.com/earth-engine/guides>`__ with different methods to process geospatial objects.

The **geetools** package extends the Google Earth Engine Python API with pre-processing and processing tools for the most used satellite platforms by adding utility methods for different Earth Engine Objects that are friendly with the Python method chaining using the ``geetools`` namespace.

content
-------

.. grid:: 1 2 3 3

   .. grid-item::

      .. card:: Usage
         :link: usage/install.html

         Usage and installation

   .. grid-item::

      .. card:: Contribute
         :link: usage/contribute.html

         Help us improve the lib.

   .. grid-item::

      .. card:: API
         :link: autoapi/index.html

         Discover the lib API.

Why using it ?
--------------

New utility methods and constructors are added to most of the GEE classes. They can be simple wrapper for repetitive tasks, complex algorithm or mandatory preprocessing steps. The goal is to make the code more fluid and easy to read for researchers, students and analysts.

The package design is mostly performing server-side computation making it also very friendly with commercial users of Earth Engine.

This small example wrapping of the excellent ``ee_extra`` package functionalities shows how to preprocess sentinel 2 data in 5 lines of code:

.. code-block:: python

   import ee
   import geetools #noqa: F401
   import pygaul # another gee-community package to access FAO GAUl 2015 dataset

   # we assume you are already authenticated to GEE
   ee.Initialize.geetools.from_account("toto") # yes we also support multi users

   amazonas = pygaul.Items(name="Amazonas").centroid()

   S2 = (
      ee.ImageCollection('COPERNICUS/S2_SR')
      .filterBounds(point)
      .geetools.closest('2020-10-15') # Extended (pre-processing)
      .geetools.maskClouds(prob = 70) # Extended (pre-processing)
      .geetools.scaleAndOffset() # Extended (pre-processing)
      .geetools.spectralIndices(['NDVI','NDWI','BAIS2'])) # Extended (processing)

