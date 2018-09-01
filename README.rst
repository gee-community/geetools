Google Earth Engine tools
#########################

These are a set of tools for Google Earth Engine that may help
to solve or automatize some processes.

There are some JavaScript functions that you can use in the Code Editor
(https://code.earthengine.google.com/) placed in a folder called ``js``

The rest of the repository is oriented to the GEE Python API. You can install
these tools as a normal python package.

Installation
============

.. code:: bash

    pip install geetools

Upgrade
=======

.. code:: bash

    pip install --upgrade geetools

Basic Usage
===========

.. code:: python

    from geetools import batch

    col = ee.ImageCollection("your_ID")
    tasklist = batch.ImageCollection.toDrive(col)

Full documentation
==================

http://geetools.readthedocs.io

Some Examples
=============

Examples are Jupyter Notebooks in a folder called `notebooks`

Any contribution is welcome.
Any bug or question please use the `github issue tracker`__.

.. _issues: https://github.com/gee-community/gee_tools/issues

__ issues_
