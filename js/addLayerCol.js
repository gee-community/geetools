/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 
PURPOSE:
This function adds all images of a collection to the Map with the given
visualization parameters

EXAMPLE:
var viz = {bands:["B5","B4","B6"], min:0, max:5000}
addLayerCol(collection, viz)
*/

var addLayerCol = function(col, viz) {
  var lista = col.getInfo()["features"]
  for (var i = 0; i < lista.length; i++) {
    var id = lista[i]["id"]
    var img = ee.Image(id)
    Map.addLayer(img, viz,id)
  }
}
