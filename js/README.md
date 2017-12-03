# JavaScript Snippets for Earth Engine's Code Editor

## Adding all images from a Collection to the Map

1. Copy the code from addLayerCol.js to the code editor (at the top of the script)
2. Create an ImageCollection, filter, etc, until you get what you want, like:

`var col = ee.ImageCollection("SOME_ID")`

3. Difine a visualization object, like:

`var viz = {bands:["B4", "B5", "B3"], min:0, max:0.7}`

4. Use the function, like:

`addLayerCol(col, viz, false, "ID")`

where:

- col = the image collection
- viz = the visualization object
- false = indicates that images won't be active at first (otherwise it could crush)
- "ID" = the names of the images will be the IDs (there are other options, see addLayerCol.js)
