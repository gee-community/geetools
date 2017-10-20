/* 
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 * email: fitoprincipe82 at gmail dot com
 
Purpose: Reclassification

HOW TO USE
There are 2 functions:
function reclass(geom, bef, aft, clasif)
   You have to create a feature collection (polygon) with a property called "clas" set to 1
   Within the polygons in the fc, the pixels with value 'bef' will be reclassified to 'aft'
   The argument 'clasif' has to be the classification to reclassify.
   Returns the new classification
   Ej: var newclas = reclass(one2two, 1, 2, class)
   
function fill(geom, val, clasif)
   You have to create a feature collection (polygon) with a property called "clas" set to 1
   Within the polygons in the fc, all the pixels will be reclassified to 'val'
   The argument 'clasif' has to be the classification to reclassify.
   Returns the new classification
   Ej: var newclas = reclass(two, 2, class)
*/
   
var reclass = function(geom, bef, aft, clasif) {
  var binario = geom.reduceToImage(["clas"], ee.Reducer.first())
  var condicion = binario.and(clas.eq(bef))
  var clasC = clasif.where(condicion, aft)
  return clasC
}

var fill = function(geom, val, clasif) {
  var binario = geom.reduceToImage(["clas"], ee.Reducer.first())
  var clasC = clasif.where(binario, val)
  return clasC
}
