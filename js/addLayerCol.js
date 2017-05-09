/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 
PURPOSE:
This function adds all images from one Collection to the Map

PARAMETERS:
col    = collection that contains the images (ImageCollection)
viz    = visualization parameters (dict)
active = (optional) whether the added layers should be active or not (bool)
         (default = true)

EXAMPLE:
var viz = {bands:["B5","B4","B6"], min:0, max:5000}
addLayerCol(collection, viz)
*/

var addLayerCol = function(col, viz, active) {
  var lista = col.getInfo()["features"];
  var active = active || true;
  for (var i = 0; i < lista.length; i++) {
    var id = lista[i]["id"]
    var img = ee.Image(id)
    Map.addLayer(img, viz, id, active)
  }
}
