Quickstart
==========



An extension ?
--------------

**geetools** is an extension package. It means that it cannot be used without the **Google Earth Engine Python API** but also that you don't need to call it explicitly to use all the methods and functions available.

To summarize, these functions are added to GEE objects inside a member called ``geetools``.

The first step is as always to authenticate to GEE and import the **geetools** package.

.. code-block:: python

    import ee
    import geetools #noqa: F401

    ee.Initialize()

At this stage all the methods of the package have been added to the ``ee`` objects. You can use them as if they were part of the original API in the ``geetools`` member.

The following example will use the ``truncate`` method to truncate a number to a given number of decimals.

.. code-block:: python
    :emphasize-lines: 2, 5

    import ee
    import geetools #noqa: F401

    number = ee.Number(3.14159265359)
    truncated = number.geetools.truncate(2)
    truncated.getInfo()

Real life example
-----------------

This small example shows how **geetools** is wrapping the excellent ``ee_extra`` package functionalities to preprocess sentinel 2 data in 5 lines of code:

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

More examples of more complex and meaningful analysis can be found in the :doc:`../example/index` gallery.

F401 ?
------

In Python it's recommended to clean you code using automatic tools like ``flake8``, ``ruff``, ``isort``...etc

These tool will raise an error if you import a package and don't use it, it's the ``F401`` error. In some tools the erroring lines can be deleted from the file. This will break your code as even if the **geetools** package is never called it's required to import it to extend the ``ee`` package.

The ``#noqa: F401`` comment is used to avoid the linter to raise an error when the package is imported but not used. It is not mandatory if you don't use linters but it is a good practice to keep your code clean.

.. note::

    as per flake8 `documentation <https://www.flake8rules.com/rules/F401.html>`__:

        F401: A module has been imported but is not used anywhere in the file. The module should either be used or the import should be removed.
