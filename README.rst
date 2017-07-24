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


Any contribution is welcome.

Any bug or question please use the github issue tracker.
