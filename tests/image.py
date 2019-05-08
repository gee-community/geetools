# coding=utf-8

import ee
from geetools import tools
ee.Initialize()


l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")

p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])


def test_addConstantBands():
    newimg = tools.image.addConstantBands(l8SR, 0, "a", "b", "c")
    vals = tools.image.getValue(newimg, p_l8SR_no_cloud, 30, 'client')

    assert vals["B1"] == 517
    assert vals["a"] == 0
    assert vals["b"] == 0
    assert vals["c"] == 0

    newimg2 = tools.image.addConstantBands(l8SR, a=0, b=1, c=2)
    vals2 = tools.image.getValue(newimg2, p_l8SR_no_cloud, 30, 'client')

    assert vals2["B1"] == 517
    assert vals2["a"] == 0
    assert vals2["b"] == 1
    assert vals2["c"] == 2

    newimg3 = tools.image.addConstantBands(l8SR, 0, "a", "b", "c", d=1, e=2)
    vals3 = tools.image.getValue(newimg3, p_l8SR_no_cloud, 30, 'client')

    assert vals3["B1"] == 517
    assert vals3["a"] == 0
    assert vals3["b"] == 0
    assert vals3["c"] == 0
    assert vals3["d"] == 1
    assert vals3["e"] == 2


def test_replace():
    # constant image with value 10 and name 'anyname'
    testband = ee.Image.constant(10).select([0],["anyname"])

    # replace band B1 of l8SR for the testband
    newimg = tools.image.replace(l8SR, "B1", testband)

    # get a value from a point with no clouds
    vals = tools.image.getValue(newimg, p_l8SR_no_cloud, 30, 'client')

    # assert
    assert vals["anyname"] == 10


def test_sumBands():
    newimg = tools.image.sumBands(l8SR, "added_bands", ("B1", "B2", "B3"))

    vals = tools.image.getValue(newimg, p_l8SR_no_cloud, 30, 'client')
    suma = int(vals["B1"]) + int(vals["B2"]) + int(vals["B3"])

    assert vals["added_bands"] == suma
    

def test_rename_bands():
    # Check original
    original_bands = l8SR.bandNames().getInfo()
    assert original_bands == ["B1", "B2", "B3", "B4", "B5", "B6", "B7",
                              "cfmask", "cfmask_conf"]

    # rename
    i = tools.image.renameDict(l8SR, {"B1": "BLUE", "B2": "GREEN"})

    # get value from point in a cloud free zone
    vals = tools.image.getValue(i, p_l8SR_no_cloud, 30, 'client')

    # get new band names
    bands = i.bandNames().getInfo()

    expected = ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
                "cfmask", "cfmask_conf"]

    assert bands == expected
    assert vals["BLUE"] == 517


def test_parametrize():
    # parametrize
    newimg = tools.image.parametrize(l8SR, (0, 10000), (0, 1), ["B1", "B2"])

    # get a value
    vals = tools.image.getValue(newimg, p_l8SR_no_cloud, 30, 'client')

    # assert
    assert vals["B1"] == 517.0/10000
    assert vals["B2"] == 580.0/10000
    assert vals["B3"] == 824


def test_minscale():
    minscale = tools.image.minscale(l8SR).getInfo()

    # assert
    assert minscale == 30


def test_pass_prop():
    empty1 = ee.Image.constant(0)
    empty2 = ee.Image.constant(0).set("satellite", "None")

    pass1 = tools.image.passProperty(l8SR, empty1, ["satellite", "WRS_PATH"])
    pass2 = tools.image.passProperty(l8SR, empty2, ["satellite", "WRS_PATH"])

    assert pass1.get("satellite").getInfo() == "LANDSAT_8"
    assert pass2.get("satellite").getInfo() == "LANDSAT_8"
    assert pass1.get("WRS_PATH").getInfo() == 231
    assert pass2.get("WRS_PATH").getInfo() == 231
