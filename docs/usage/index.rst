Guides
======

Overview
--------

This section gathered many real life examples of the Lib usage gathered by the community.
If you think your workflow should be shared please open a PR and follow the contribution guildelines shared in the next section.

.. warning::

    The example gallery is a work in progress as the library was recently refactored.
    All contributions are welcolmed!

Add a new example
-----------------

.. image:: /_static/we-need-you.jpg
    :alt: We need you!
    :align: center

Currently most of the examples built by `@Rodrigo <https://github.com/fitoprincipe>`__ are still using the old implementation of the library.
They should be transformed into modern example and moved from the old `notebook <https://github.com/gee-community/geetools/tree/main/notebooks>`__ folder to the new `example <https://github.com/gee-community/geetools/tree/main/docs/example>`__ one to be displayed in our doc.

The examples are regular notebook files that are interpreted by the ``myst-nb`` lib and displayed in the doc, clicking on the :guilabel:`open in colab` button will open a colab notebook with the code ready to be executed and the :guilabel:`view source` will bring you back to github.

To add a new example, you can use the `example template <https://github.com/gee-community/geetools/tree/main/docs/usage/template.ipynb>`__ and replace things with your code.

Adapt the code of the 2 first buttons to your file so users can lunch it in collab and view the source in github.

.. code-block:: md

    [![github](https://img.shields.io/badge/-see%20sources-white?logo=github&labelColor=555)](https://github.com/gee-community/geetools/blob/main/docs/usage/template.ipynb)
    [![colab](https://img.shields.io/badge/-open%20in%20colab-blue?logo=googlecolab&labelColor=555)](https://colab.research.google.com/github/gee-community/geetools/blob/main/docs/usage/template.ipynb)


Then you can open a PR with the new file and it will be reviewed and merged.

.. toctree::
    :hidden:

    template
    export
    plot/index
    asset
    profile
    reduce