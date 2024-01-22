.. warning::

    This package is under heavy refactoring.
    If you want to access the previous version, please have a look to the `0.x` branch
    We also start to make pre-release so people can try the latest version. Have a look to the `pypi page <https://pypi.org/project/geetools/>`__ to stay up-to-date.

Google Earth Engine tools
-------------------------

.. image:: docs/_static/logo.svg
    :width: 20%
    :align: right

These are a set of tools for working with Google Earth Engine Python API that may help to solve or automate some processes.

There is JavaScript module that you can import from the code editor that has
similar functions (not exactly the same) and it's available `here <https://github.com/fitoprincipe/geetools-code-editor>`__.

Installation
------------

.. code-block:: python

    pip install geetools

Basic Usage
-----------

Export every image in a ``ee.ImageCollection``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-blcok:: python

    import ee
    import geetools

    ee.Initialize()

    # Define an ImageCollection

    site = ee.Geometry.Point([-72, -42]).buffer(1000)
    collection = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").filterBounds(site).limit(5)

    # Set parameters
    bands = ['B2', 'B3', 'B4']
    scale = 30
    name_pattern = '{sat}_{system_date}_{WRS_PATH:%d}-{WRS_ROW:%d}'

    ## the keywords between curly brackets can be {system_date} for the date of the
    ## image (formatted using `date_pattern` arg), {id} for the id of the image
    ## and/or any image property. You can also pass extra keywords using the `extra`
    ## argument. Also, numeric values can be formatted using a format string (as
    ## shown in {WRS_PATH:%d} (%d means it will be converted to integer)
    date_pattern = 'ddMMMy' # dd: day, MMM: month (JAN), y: year
    folder = 'MYFOLDER'
    data_type = 'uint32'
    extra = dict(sat='L8SR')
    region = site

    # Export
    tasks = geetools.batch.Export.imagecollection.toDrive(
        collection=collection,
        folder=folder,
        region=site,
        namePattern=name_pattern,
        scale=scale,
        dataType=data_type,
        datePattern=date_pattern,
        extra=extra,
        verbose=True,
        maxPixels=int(1e13)
    )

Some useful functions
^^^^^^^^^^^^^^^^^^^^^

batch exporting
###############

- Export every image in an ImageCollection to Google Drive, GEE Asset or Cloud Storage `examples <https://github.com/gee-community/gee_tools/tree/master/notebooks/batch>`__
- Clip an image using a FeatureCollection and export the image inside every Feature `example <https://github.com/gee-community/gee_tools/tree/master/notebooks/batch>`__

Image processing
################

- Pansharp `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/algorithms/pansharpen.ipynb>`__
- Mask pixels around masked pixels (buffer around a mask) `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/image/bufferMask.ipynb>`__
- Get the percentage of masked pixels inside a geometry `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/algorithms/mask_cover.ipynb>`__
- Cloud masking functions `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/cloud_mask/cloud_masking.ipynb>`__

Compositing
###########

- Closest date composite: replace masked pixels with the "last available not masked pixel" `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/composite/closest_date.ipynb>`__
- Medoid composite `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/composite/medoid.ipynb>`__

Image Collections
#################

- Mosaic same day `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/imagecollection/mosaicSameDay.ipynb>`__

Visualization
#############

- Get visualization parameters using a stretching function `example <https://github.com/gee-community/gee_tools/blob/master/notebooks/visualization/stretching.ipynb>`__

All example Jupyter Notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Jupyter Notebooks avilables `here <https://github.com/gee-community/gee_tools/tree/master/notebooks>`__

Contributing
------------

Any contribution is welcome.
Any bug or question please use the `github issue tracker https://github.com/gee-community/gee_tools/issues`__
