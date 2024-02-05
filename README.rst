geetools
========

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative&logoColor=white
    :target: LICENSE
    :alt: License: MIT

.. image:: https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg?logo=git&logoColor=white
    :target: https://conventionalcommits.org
    :alt: conventional commit

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black badge

.. image:: https://img.shields.io/badge/code_style-prettier-ff69b4.svg?logo=prettier&logoColor=white
    :target: https://github.com/prettier/prettier
    :alt: prettier badge

.. image:: https://img.shields.io/badge/pre--commit-active-yellow?logo=pre-commit&logoColor=white
    :target: https://pre-commit.com/
    :alt: pre-commit

.. image:: https://img.shields.io/pypi/v/geetools?color=blue&logo=pypi&logoColor=white
    :target: https://pypi.org/project/geetools/
    :alt: PyPI version

.. image:: https://img.shields.io/github/actions/workflow/status/gee-community/geetools/unit.yaml?logo=github&logoColor=white
    :target: https://github.com/gee-community/geetools/actions/workflows/unit.yaml
    :alt: build

.. image:: https://img.shields.io/codecov/c/github/gee-community/geetools?logo=codecov&logoColor=white
    :target: https://codecov.io/gh/gee-community/geetools
    :alt: Test Coverage

.. image:: https://img.shields.io/readthedocs/gee-tools?logo=readthedocs&logoColor=white
    :target: https://gee-tools.readthedocs.io/en/latest/
    :alt: Documentation Status

Google Earth Engine tools
-------------------------

.. image:: https://raw.githubusercontent.com/gee-community/geetools/main/docs/_static/logo.svg
    :width: 20%
    :align: right

`Google Earth Engine <https://earthengine.google.com/>`__ is a cloud-based service for geospatial processing of vector and raster data. The Earth Engine platform has a `JavaScript and a Python API <https://developers.google.com/earth-engine/guides>`__ with different methods to process geospatial objects.

The **geetools** package extends the Google Earth Engine Python API with pre-processing and processing tools for the most used satellite platforms by adding utility methods for different Earth Engine Objects that are friendly with the Python method chaining using the ``geetools`` namespace.

There is JavaScript module that you can import from the code editor that has
similar functions (not exactly the same) and it's available `here <https://github.com/fitoprincipe/geetools-code-editor>`__.

Installation
------------

.. code-block:: python

    pip install geetools

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
