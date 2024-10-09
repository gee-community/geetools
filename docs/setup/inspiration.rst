Aknowledgment
=============

This project was inspired by other very cool initiatives and we would like to acknowledge them here.

xarray
------

the `xarray <https://docs.xarray.dev/en/stable/index.html>`__ lib is a great lib to handle n-dimensional data and has very well documented the use of the extension pattern. Without their guidances, `documentation <https://docs.xarray.dev/en/stable/internals/extending-xarray.html>`__ and `sphinx-extention <https://sphinx-autosummary-accessors.readthedocs.io>`__, this project would have not been possible.

eemont
------

the `eemont <https://eemont.readthedocs.io>`__ lib has already implemented the extension pattern and allow the users to perform many different operations from preprocessing to extra construction methods. We loved some of them so much that we rewired within **geetools** every method available in `ee_extra <https://ee-extra.readthedocs.io>`__.

Our implementations diverge on 2 main points:

- We decided to be more careful with the extensions and avoid adding them directly after the ``earthengine-api`` objects. We preferred to follow ``xarray`` recommendation and create systematically a ``geetools`` intermediate member to notify to the user that no, these methods are not from the vanilla ``earthengine-api`` but from the ``geetools`` lib.

- We decided not to reimplement the Python magic methods. Now that EarthEngine is a commercial product, the users need to always be in control of what is performed server-side and what is performed client-side. We believe that spercharging magic method (although they allow cool things as ``ee.Image(1) + ee.image(2)``) make it even more confusing for new users to understand what is performed server-side and what is performed client-side. That's why all our method are using camel case naming convention and only return ``ee.ComputedObject``. Few exceptions are made for converters and plotting method that are forced to run an interactive ``getInfo()`` but they use snake case convention to notify their user and have a disclaimer in the docstring.
