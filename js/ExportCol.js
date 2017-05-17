/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 
PURPOSE:
This function Exports all images from one Collection

PARAMETERS:
col = collection that contains the images (ImageCollection)
folder = the folder where images will go (str) (optional)
scale = the pixel's scale (int) (optional) (defaults to 1000) (for Landsat use 30)
maxPixels = max number of pixels to include in the image (int) (optional)
region = the region where images are on (Geometry.LinearRing or Geometry.Polygon) (optional)

Be careful with the region parameter. If the collection has images 
in different regions I suggest not to set that parameter

EXAMPLE:
ExportCol(myLandsatCol, "Landsat_imgs", 30)
*/

var ExportCol = function(col, folder, scale, maxPixels, region) {
  
  var colinfo = col.getInfo();  
  var feat = colinfo["features"];
  var idcol = colinfo["id"]
  var idcol_len = idcol.length;
  var name = idcol.split("/").join("-");
  //description = description || "myExportImageTask";
  folder = folder || name;
  scale = scale || 1000;
  maxPixels = maxPixels || 1e10;
  for (var i = 0; i < feat.length; i++) {
    var id = feat[i]["id"]
    var idimg = id
    var img = ee.Image(id)
    region = region || img.geometry().bounds().getInfo()["coordinates"]
    var img_name = idimg.slice(idcol_len+1)
    Export.image.toDrive({
      image:img, 
      description: img_name,
      folder: folder, 
      fileNamePrefix: img_name, 
      region: region, 
      scale: scale, 
      maxPixels: maxPixels})
  }
}
