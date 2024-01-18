> :warning: **Warning** :warning:  
> This package is under heavy refactoring.
> If you want to access the previous version, please have a look to the `0.x` branch
> We also start to make pre-release so people can try the latest version. Have a look to the [pypi page](https://pypi.org/project/geetools/) to stay up-to-date.  
> :warning: **Warning** :warning:

# Google Earth Engine tools

These are a set of tools for working with Google Earth Engine Python API that
may help to solve or automate some processes.

There is JavaScript module that you can import from the code editor that has
similar functions (not exactly the same) and it's available [here](https://github.com/fitoprincipe/geetools-code-editor)

### Note for old users

#### New version 0.3.0

I have split this package in two. This `geetools` will contain functions and
methods related to Google Earth Engine exclusively, so you can use this module
in any python environment you like. For working in Jupyter I have made another
package called `ipygee` available [here](http://www.github.com/fitoprincipe/ipygee)

#### New version 0.5.0 (breaking changes)

I have split this package in two (again). Now the functions to make a strip
of images using Pillow is available as a different package called [`geepillow`](https://github.com/fitoprincipe/geepillow)

#### New version 0.6.0 (breaking changes)

I have split this package in two (again x2). The module `geetools.collection`
in an independent package called [geedataset](https://github.com/fitoprincipe/geedatasets)

## Installation

    pip install geetools

## Upgrade

    pip install --upgrade geetools

## Basic Usage

### Export every image in a ImageCollection

```python
import ee
ee.Initialize()
import geetools

# ## Define an ImageCollection
site = ee.Geometry.Point([-72, -42]).buffer(1000)
collection = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").filterBounds(site).limit(5)

# Set parameters
bands = ['B2', 'B3', 'B4']
scale = 30
name_pattern = '{sat}_{system_date}_{WRS_PATH:%d}-{WRS_ROW:%d}'
## the keywords between curly brackets can be {system_date} for the date of the
## image (formatted using `date_pattern` arg), {id} for the id of the image
## and/or any image property. You can also pass extra keywords using the `extra`
## argument. Also, numeric values can be formatted using a format string (as
## shown in {WRS_PATH:%d} (%d means it will be converted to integer)
date_pattern = 'ddMMMy' # dd: day, MMM: month (JAN), y: year
folder = 'MYFOLDER'
data_type = 'uint32'
extra = dict(sat='L8SR')
region = site

# ## Export
tasks = geetools.batch.Export.imagecollection.toDrive(
            collection=collection,
            folder=folder,
            region=site,
            namePattern=name_pattern,
            scale=scale,
            dataType=data_type,
            datePattern=date_pattern,
            extra=extra,
            verbose=True,
            maxPixels=int(1e13)
        )
```

## Some useful functions

### batch exporting

- Export every image in an ImageCollection to Google Drive, GEE Asset or Cloud Storage [examples](https://github.com/gee-community/gee_tools/tree/master/notebooks/batch)
- Clip an image using a FeatureCollection and export the image inside every Feature [example](https://github.com/gee-community/gee_tools/tree/master/notebooks/batch)

### Image processing

- Pansharp [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/algorithms/pansharpen.ipynb)
- Mask pixels around masked pixels (buffer around a mask) [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/image/bufferMask.ipynb)
- Get the percentage of masked pixels inside a geometry [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/algorithms/mask_cover.ipynb)
- Cloud masking functions [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/cloud_mask/cloud_masking.ipynb)

### Compositing

- Closest date composite: replace masked pixels with the "last available not masked pixel" [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/composite/closest_date.ipynb)
- Medoid composite [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/composite/medoid.ipynb)

### Image Collections

- Mosaic same day [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/imagecollection/mosaicSameDay.ipynb)

### Visualization

- Get visualization parameters using a stretching function [example](https://github.com/gee-community/gee_tools/blob/master/notebooks/visualization/stretching.ipynb)

## All example Jupyter Notebooks

Jupyter Notebooks avilables [here](https://github.com/gee-community/gee_tools/tree/master/notebooks)

## Contributing

Any contribution is welcome.
Any bug or question please use the [`github issue tracker`](https://github.com/gee-community/gee_tools/issues)

## Star History

<a href="https://star-history.com/#gee-community/gee_tools&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=gee-community/gee_tools&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=gee-community/gee_tools&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=gee-community/gee_tools&type=Date" />
  </picture>
</a>
