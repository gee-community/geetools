/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 * email: fitoprincipe82@gmail.com
 
PURPOSE:
This function Exports all images from one Collection

PARAMETERS:
col = collection that contains the images (ImageCollection) (not optional)
folder = the folder where images will go (str) (not optional)

scale = the pixel's scale (int) (optional) (defaults to 1000) (for Landsat use 30)
type = data type of the exported image (str) (option: "float", "byte", "int", "double") (optional) (defaults to "float")
nimg = number of images of the collection (can be greater than the actual number) (int) (optional) (defaults to 500)
maxPixels = max number of pixels to include in the image (int) (optional) (defults to 1e10)
region = the region where images are on (Geometry.LinearRing or Geometry.Polygon) (optional) (defaults to the image footprint)

Be careful with the region parameter. If the collection has images 
in different regions I suggest not to set that parameter

EXAMPLE:
ExportCol(myLandsatCol, "Landsat_imgs", 30)
*/

var ExportCol = function(col, folder, scale, type,
                         nimg, maxPixels, region) {
    type = type || "float";
    nimg = nimg || 500;
    scale = scale || 1000;
    maxPixels = maxPixels || 1e10;
    
    var colList = col.toList(nimg);
    var n = colList.size().getInfo();
    
    for (var i = 0; i < n; i++) {
      var img = ee.Image(colList.get(i));
      var id = img.id().getInfo();
      region = region || img.geometry().bounds().getInfo()["coordinates"];
      
      var imgtype = {"float":img.toFloat(), 
                     "byte":img.toByte(), 
                     "int":img.toInt(),
                     "double":img.toDouble()
                    }
      
      Export.image.toDrive({
        image:imgtype[type],
        description: id,
        folder: folder,
        fileNamePrefix: id,
        region: region,
        scale: scale,
        maxPixels: maxPixels})
    }
  }
