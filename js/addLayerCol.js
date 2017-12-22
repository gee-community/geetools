/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 * email: fitoprincipe82@gmail.com
 
PURPOSE:
This function adds all images from one Collection to the Map. You can label
the images using any available property or choosing between "date" or "ID"

PARAMETERS:
col    = collection that contains the images (ImageCollection)
viz    = visualization parameters (dict)
active = whether the added layers should be active or not (bool)
label  = label of the layer. Can be the name of a property or one of "date" or
         "ID"

EXAMPLE:
var collection = ee.ImageCollection("LANDSAT/LC8_L1T_TOA")
var viz = {bands:["B5","B4","B6"], min:0, max:0.5}
addLayerCol(collection, viz, false, "date")
*/

var addLayerCol = function(col, viz, active, label) {
  var label = label;
  var n = col.size().getInfo();
  var list = col.toList(n);
  var active = active;
  for (var i = 0; i < n; i++) {
    var img = ee.Image(list.get(i));
    if (label == "ID") {
      var id = img.id().getInfo();
      var laylabel = label+" "+id;
    } else if (label == "system_date") {
      var date = img.date().format().getInfo()
      var laylabel = label+" "+date;
    } else if (img.propertyNames().contains(label).getInfo() == true) {
      var p = img.get(label).getInfo();
      var laylabel = label+" "+p
    } else {
      print(label+" not found")
      var laylabel = "No. "+i.toString();
    }
    Map.addLayer(img, viz, laylabel, active)
  }
}
