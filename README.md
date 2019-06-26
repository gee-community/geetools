# Google Earth Engine tools

These are a set of tools for working with Google Earth Engine Python API that
may help to solve or automatize some processes.

There is JavaScript module that you can import from the code editor that has
similar functions (not exactly the same) and it's available [here](https://github.com/fitoprincipe/geetools-code-editor)

### Note for old users
#### New version 0.3.0
I have splitted this package in two. This `geetools` will contain functions and
methods related to Google Earth Engine exclusively, so you can use this module
in any python environment you like. For working in Jupyter I have made another
package called `ipygee` available [here](http://www.github.com/fitoprincipe/ipygee) 


## Installation

    pip install geetools

## Upgrade

    pip install --upgrade geetools

## Basic Usage

``` python
from geetools import batch

col = ee.ImageCollection("your_ID")
tasklist = batch.Export.imagecollection.toDrive(col)
```

## Examples

Jupyter Notebooks avilables [here](https://github.com/gee-community/gee_tools/tree/master/notebooks)

## Contributing

Any contribution is welcome.
Any bug or question please use the [`github issue tracker`](https://github.com/gee-community/gee_tools/issues)
