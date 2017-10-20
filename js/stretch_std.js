/*
 * Author: Rodrigo E. Principe
 * License: Apache 2.0
 * email: fitoprincipe82 at gmail dot com

PURPOSE:
Get streched values of bands using the standard deviation,
to use in visualization

PARAMETERS:
n_std: number of standard deviations from mean.
       min: mean-(n_std*std)
       max: mean+(n_std*std)

RETURNS:
A JavaScript Object, so access throught dot notation. See in the example:
s.vmin.B5, s.vmax.B5, etc

EXAMPLE:

var i = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013296LGN00")
var s = stretch_std(3)

var min = ee.Number(ee.List([s.vmin.B5, s.vmin.B6, s.vmin.B4]).reduce(ee.Reducer.mean()))
var max = ee.Number(ee.List([s.vmax.B5, s.vmax.B6, s.vmax.B4]).reduce(ee.Reducer.mean()))

var viz = {bands:["B5", "B6", "B4"],
           min: min.getInfo(),
           max: max.getInfo()}

var vizEE = {bands:["B5", "B6", "B4"],
           min: -0.06102305441591904,
           max: 0.41922686174360246}

print(viz)

Map.addLayer(i, {bands:["B5", "B6", "B4"],
                 min:0, max:1}, "not streched")

Map.addLayer(i, vizEE, "streched by EE")
Map.addLayer(i, viz, "streched by gee_tools")
*/

var stretch_std = function(n_std) {
  var mean = i.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: i.geometry(),
    bestEffort: true})
  var std = i.reduceRegion({
    reducer: ee.Reducer.stdDev(),
    geometry: i.geometry(),
    bestEffort: true})
  var min = mean.map(function(key, val){
      return ee.Number(val).subtract(ee.Number(std.get(key)).multiply(n_std))
    }).getInfo()
  var max = mean.map(function(key, val){
      return ee.Number(val).add(ee.Number(std.get(key)).multiply(n_std))
    }).getInfo()

  return {vmin: min, vmax: max}
}