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

    from geetools import tools

    col = ee.ImageCollection("your_ID")
    tasklist = tools.col2asset(col)

Full documentation
==================

http://geetools.readthedocs.io

Some Examples
=============

execli
------
Executes a client-side function (e.g. ``getInfo`` ) as many time as needed and
waits between each call as much as needed.

.. code:: python

        from geetools.tools import execli
        import ee

        # This image doesn't exist so it will throw an error
        img = ee.Image("wrongparam")

        # try to get the info with default parameters (10 times, wait 0 sec)
        info = execli(img.getInfo)()
        print info

        # try with custom param (2 times 5 seconds with traceback)
        info2 = execli(img.getInfo, 2, 5, True)
        print info2

execli_deco
-----------
Performs the same action as ``execli`` but is meant to be used as a decorator.

.. code:: python

        from geetools.tools import execli_deco
        import ee

        # TRY TO GET THE INFO OF AN IMAGE WITH DEFAULT PARAMETERS

        @execli_deco()
        def info():
            # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
            img = ee.Image("wrongparam")

            return img.getInfo()

        # TRY WITH CUSTOM PARAM (2 times 5 seconds and traceback)

        @execli_deco(2, 5, True)
        def info():
            # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
            img = ee.Image("wrongparam")

            return img.getInfo()

addConstantBands
----------------
Adds constant bands to an image. You can use it in 3 ways (see example below)

.. code:: python

        from geetools.tools import addConstantBands
        import ee

        col = ee.ImageCollection(ID)

        # Option 1 - arguments
        addC = addConstantBands(0, "a", "b", "c")
        newcol = col.map(addC)

        # Option 2 - keyword arguments
        addC = addConstantBands(a=0, b=1, c=2)
        newcol = col.map(addC)

        # Option 3 - Combining
        addC = addC = addConstantBands(0, "a", "b", "c", d=1, e=2)
        newcol = col.map(addC)

Any contribution is welcome.
Any bug or question please use the `github issue tracker`__.

.. _issues: https://github.com/gee-community/gee_tools/issues

__ issues_
