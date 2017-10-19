/*
 * Author: Rodrigo E. Principe
 * License: Apache 2.0

PURPOSE:
To filter a FeatureCollection made of Points within a 'buffer' distance

PARAMETERS:
points: FeatureCollection containing the points to filter
distance: The distance of the buffer (If no projection is specified, the unit
          is meters. Otherwise the unit is in the coordinate system of the
          projection.

EXAMPLE:
var geometry = ee.Geometry.Polygon([[
    [-72,-46], [-72,-42], [-63, -42], [-63, -46]]]);
var fcRandomPoints = ee.FeatureCollection.randomPoints(geometry, 200, 5);

var filtered = filterDistance(fcRandomPoints, 50000)
*/

var filterDistance = function(points, distance) {
  var filt2 = ee.List([])
  var filt = points.iterate(function(el, ini){
                         var ini = ee.List(ini)
                         var fcini = ee.FeatureCollection(ini)
                         var buf = ee.Feature(el).geometry().buffer(distance)
                         var s = fcini.filterBounds(buf).size()
                         var cond = s.lte(0)
                         return ee.Algorithms.If(cond, ini.add(el), ini)
                       }, filt2)
  var filtered = ee.FeatureCollection(ee.List(filt))
  return filtered
}