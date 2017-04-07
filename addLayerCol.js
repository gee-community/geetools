/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 
HOW TO USE
This function adds all images of a collection to the Map with the given
visualization parameters

USAGE:
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
