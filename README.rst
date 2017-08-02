Google Earth Engine tools
#########################

These are a bunch of Google Earth Engine Scripts with some tools that may help
to solve or automatize some processes. The JavaScript scripts here can only be
pasted to the code editor.

For the Python module, clone the repository and copy the folder *gee_tools_py*
to the folder you have the scripts. As it is a module, you can import it
direcltly like:

``from gee_tools_py import geetools as gee``

and then you can use it:

.. code:: python

    from gee_tools_py import geetools as gee

    col = ee.ImageCollection("your_ID")
    tasklist = gee.col2asset(col)

Function's Examples
-------------------

``execli``

.. code:: python

        from geetools import execli
        import ee
        ee.Initialize()

        # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
        img = ee.Image("wrongparam")

        # try to get the info with default parameters (10 times, wait 0 sec)
        info = execli(img.getInfo)()
        print info

        # try with custom param (2 times 5 seconds with traceback)
        info2 = execli(img.getInfo, 2, 5, True)
        print info2

``execli_deco``

.. code:: python

        from geetools import execli_deco
        import ee
        ee.Initialize()

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

Any contribution is welcome.

Any bug or question please use the github issue tracker.
