The extension pattern
=====================

.. note::

    This page is vastly inspired from the ``xarray`` `documentation <https://docs.xarray.dev/en/stable/internals/extending-xarray.html>`__ that is the inspiration for the ``geetools`` implementation.

**Google Earth Engine** is designed as a general purpose library and hence tries to avoid including overly user specific functionality. But inevitably, the need for open-source community to contribute arises. This is where the extension pattern comes in.

Composition over Inheritance
----------------------------

One potential solution to this problem is to subclass every ``ee.ComputedObject`` to add user specific functionality. However, inheritance is not very robust. It’s easy to inadvertently use internal APIs when subclassing, which means that your code may break when ``earthengine-api`` upgrades. Furthermore, many builtin methods will only return native ``ee.ComputedObject`` objects.

The standard advice is to use composition over inheritance, but reimplementing an API as large as ``earthengine-api`` on your own objects can be an onerous task, even if most methods are only forwarding to ``earthengine-api`` implementations (That was the technical choice made prior in v0 of ``geetools``).


Writing Custom Accessors
------------------------

To resolve this issue for more complex cases, ``geetools`` has implemented 3 decorators:

- A class decorator: :py:meth:`register_class_accessor <geetools.accessors.register_class_accessor>`
- A function decorator: :py:meth:`register_function_accessor <geetools.accessors.register_function_accessor>`

They are used to add custom “accessors” on objects/functions/modules thereby “extending” the functionality of your ``ee`` object.

Here’s how we use these decorators to write a custom “geetools” accessor implementing a extra method to ``ee.Number`` object:

.. code-block:: python

    import ee
    from geetools.accessor import register_class_accessor

    @register_class_accessor(ee.Number, "geetools")
    class NumberAccessor:

    def __init__(self, obj: ee.Number):
        self._obj = obj

    def truncate(self, nbDecimals = 2):
        """Truncate a number to a given number of decimals."""
        nbDecimals = ee.Number(nbDecimals).toInt()
        factor = ee.Number(10).pow(nbDecimals)
        return self._obj.multiply(factor).toInt().divide(factor)

In general, the only restriction on the accessor class is that the ``__init__`` method must have a single parameter: the object it is supposed to work on.

This achieves the same result as if the Dataset class had a cached property defined that returns an instance of your class:

.. code-block:: python

    class Number:
        ...

        @property
        def geetools(self):
            return NumberAccessor(self)

However, using the register accessor decorators is preferable to simply adding your own ad-hoc property (i.e., ``ee.number.geetools = property(...)``), for several reasons:

- It ensures that the name of your property does not accidentally conflict with any other attributes or methods (including other accessors).
- Instances of accessor object will be cached on the object that creates them. This means you can save state on them (e.g., to cache computed properties).
- Using an accessor provides an implicit namespace for your custom functionality that clearly identifies it as separate from built-in ``earthengine-api`` methods.

.. note::

    Accessors are created once per object instance. New instances, like those created from mapping operations or when accessing a ``ee.Feature`` from a ``ee.FeatureCollection`` (ex. ``fc.first()``), will have new accessors created.

The intent here is that libraries that extend ``earthengine-api`` could add such an accessor to implement subclass specific functionality rather than using actual subclasses or patching in a large number of domain specific methods. For further reading on ways to write new accessors and the philosophy behind the approach, see https://github.com/pydata/xarray/issues/1080.