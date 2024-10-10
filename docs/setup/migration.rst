Upgrade from v0 to v1
=====================

in v1 **geetoold** has fully embraced the extension pattern and has revamped most of it's functionalities.
This page will gather the changes that you need to make to your code to upgrade from v0 to v1.

The lib is following a deprecation cycle of several month so no function has been directly removed.
They will simply raised a deprecation warning and provide some suggestion on the potential replacement.

None the less, as previous implementation was leading to internal issues such as circular imports, it is recommended to update your code to the new pattern as soon as possible to avoid any future breakage.

.. warning::

    This documentation is gathering problems faced by the community and the solutions that were found.
    If you have a problem that is not listed here, please open an item in our `issue tracker <https://github.com/gee-community/geetools/issues/new>`__.


Import the modules
------------------

If in the previous implementation, most of the modules were brought back to the main ``__init.py`` which was causing circular import issues.
In v1 the internal structure was revisited and some modules are no longer accecible from ``geetools``.

A v0 implementation would look like this:

.. code-block:: python

    import ee
    from geetools.tools import geometry

    image = ee.Image(ee.ImageCollection('COPERNICUS/S2').first())
    tools.geometry.getRegion(image)

It will raise an error as the "tools" file has been replaced by a "_deprecated_tools" one.

Now to run the same code you should do:

.. code-block:: python

    import ee
    from geetools import tools

    image = ee.Image(ee.ImageCollection('COPERNICUS/S2').first())
    tools.geometry.getRegion(image)

This will simply raise a deprecation warning and will work as expected.





