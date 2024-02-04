User guide
==========

Overview
--------

The User Guide covers all of **geetools** by topic area. The :doc:`quickstart` page is a good place to start if you are new to the package or just want to refresh your memory. The :doc:`layout` page provides a high-level overview of the package's layout, and the :doc:`pattern` page provides a high-level overview of the package's design decsisions.

The use of the package requires a basic understanding of the **Python** programming language and the **GEE Python API**. Users brand-new to Earth Engine should refer to the `Google documentation <https://developers.google.com/earth-engine>`__ first.

Further hands-on example of specific tasks can be found in the :doc:`../example/index` section. and for the most advance user please refe to the :doc:`../autoapi/index` section for a complete description of each individual functionality.

Refactoring
-----------

Since version v1.0.0, the package has been drastically modified to adopt the extension pattern (see :doc:`pattern` for more information). Many functions have also bee dropped or fully refactored to improve overall performances, and to make the package more consistent and easy to use. For more information about the miregation process please refer to the :doc:`migration` page.

.. important::

    The refactoring process is not finished yet, we will progressively reintegrate all the methods in the new pattern and add many cool functionalities. If any of your previous is not working anymore and the :doc:`migration` page did not provided any solution, please open an issue in the `GitHub repository <https://github.com/gee-community/geetools/issues/new>`__.

.. toctree::
    :hidden:
    :caption: Get started

    install
    quickstart
    layout

.. toctree::
    :hidden:
    :caption: Extension Layout

    pattern
    migration
    inspiration

.. toctree::
    :hidden:
    :caption: Contributor guide

    contribute
    author
    license


