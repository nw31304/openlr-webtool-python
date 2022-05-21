from geotool_4326 import GeoTool_4326
from openlr import Coordinates
from pytest import approx
from shapely.geometry import LineString
from shapely import wkt
from math import pi, sqrt, degrees, radians

gt = GeoTool_4326()
wkt1 = "LINESTRING(-95.5243893 29.8085368,-95.5243909 29.8088737)"
ls1 = wkt.loads(wkt1)
wkt2 = "LINESTRING(-97.1929155 32.9859557,-97.1931752 32.9859218,-97.193487 32.985917,-97.1937464 32.9859559,-97.1939501 32.9860045,-97.1942546 32.9861367,-97.1945905 32.9863456,-97.1948123 32.9865937,-97.1949169 32.9867542,-97.1950152 32.9869575,-97.1950816 32.9872331,-97.1951863 32.9876451,-97.1952682 32.9879134,-97.1955662 32.9886444)"
ls2 = wkt.loads(wkt2)
wkt3 = "LINESTRING(-94.2673269 32.8094417,-94.2670405 32.8091639,-94.2667164 32.8088278,-94.2665553 32.8086223,-94.2662813 32.8083671,-94.2661053 32.8082114,-94.2660887 32.8081756,-94.2660794 32.8079951,-94.266085 32.8073242,-94.2660942 32.8066316,-94.2660794 32.8063623,-94.2660387 32.8060557,-94.2659905 32.8056059,-94.2659794 32.8054549,-94.2660072 32.8052759,-94.2660664 32.8050767,-94.2660794 32.8050051,-94.2660387 32.8049537,-94.2660016 32.8049397,-94.2657998 32.8049304,-94.2656498 32.8049366,-94.2655201 32.8049802,-94.2654553 32.8049848)"
ls3 = wkt.loads(wkt3)
wkt4a = "LINESTRING(-94.876017 29.263155,-94.8755017 29.2621853,-94.875399 29.2619905)"
ls4a = wkt.loads(wkt4a)
# ls4a_len = 142.69105284339304
wkt4b = "LINESTRING(-94.875399 29.2619905,-94.8733005 29.2580099)"
ls4b = wkt.loads(wkt4b)
# ls4b_len = 487.19160540988935
wkt4c = "LINESTRING(-94.8733005 29.2580099,-94.8716434 29.254932)"
ls4c = wkt.loads(wkt4c)
# ls4c_len = 378.1212734374413
wkt4_comb = "LINESTRING(-94.876017 29.263155,-94.8755017 29.2621853,-94.875399 29.2619905,-94.8733005 29.2580099,-94.8716434 29.254932)"
ls4_comb = wkt.loads(wkt4_comb)

ls4a_len = gt.line_string_length(ls4a)
ls4b_len = gt.line_string_length(ls4b)
ls4c_len = gt.line_string_length(ls4c)

def test_bearing():
    b = gt.bearing(Coordinates(lon=ls1.coords[0][0], lat=ls1.coords[0][1]), Coordinates(lon=ls1.coords[1][0],lat=ls1.coords[1][1]))
    assert(degrees(b) == approx(-0.23730179516327252, rel=1e-7))
    b = gt.bearing(Coordinates(lon=ls1.coords[1][0], lat=ls1.coords[1][1]), Coordinates(lon=ls1.coords[0][0],lat=ls1.coords[0][1]))
    assert(degrees(b) == approx(179.76269740946745, rel=1e-7))

    b = gt.bearing(Coordinates(lon=ls2.coords[0][0], lat=ls2.coords[0][1]), Coordinates(lon=ls2.coords[1][0],lat=ls2.coords[1][1]))
    assert(degrees(b) == approx(-98.80429346948154, rel=1e-7))
    b = gt.bearing(Coordinates(lon=ls2.coords[1][0], lat=ls2.coords[1][1]), Coordinates(lon=ls2.coords[0][0],lat=ls2.coords[0][1]))
    assert(degrees(b) == approx(81.19556514121741, rel=1e-7))

    b = gt.bearing(Coordinates(lon=ls3.coords[0][0], lat=ls3.coords[0][1]), Coordinates(lon=ls3.coords[1][0],lat=ls3.coords[1][1]))
    assert(degrees(b) == approx(138.95634225020362, rel=1e-7))
    b = gt.bearing(Coordinates(lon=ls3.coords[1][0], lat=ls3.coords[1][1]), Coordinates(lon=ls3.coords[0][0],lat=ls3.coords[0][1]))
    assert(degrees(b) == approx(-41.043502565479656, rel=1e-7))

def test_transform():
    wgs1 = Coordinates(lon=-95.04189848899841, lat=29.41189169883728)
    xy1 = gt.transform_coordinate(wgs1)
    assert(xy1.lon == approx(-95.04189848899841, rel=1e-7))
    assert(xy1.lat == approx(29.41189169883728, rel=1e-7))
    
def test_distance():
    b = gt.distance(Coordinates(lon=ls2.coords[0][0], lat=ls2.coords[0][1]), Coordinates(lon=ls2.coords[1][0],lat=ls2.coords[1][1]))
    assert(b == approx(24.563082409554156, rel=1e-7))
    b = gt.distance(Coordinates(lon=ls2.coords[1][0], lat=ls2.coords[1][1]), Coordinates(lon=ls2.coords[0][0],lat=ls2.coords[0][1]))
    assert(b == approx(24.563082409554156, rel=1e-7))

def test_line_string_length():
    assert(gt.line_string_length(ls1) == approx(37.34542416957637, 1e-7))
    assert(gt.line_string_length(ls2) == approx(442.6299118813308, 1e-7))
    assert(gt.line_string_length(ls3) == approx(598.4771966218154, 1e-7))
    assert(gt.line_string_length(ls4a) == approx(142.3646031374206, 1e-7))
    assert(gt.line_string_length(ls4b) == approx(486.0726622282324, 1e-7))
    assert(gt.line_string_length(ls4c) == approx(377.2645813272347, 1e-7))

def test_extrapolate():
    x = gt.extrapolate(Coordinates(lon=ls1.coords[0][0], lat=ls1.coords[0][1]),37.34542416957637, radians(-0.23730179516327252))
    assert(x.lon == approx(-95.5243909, rel=1e-7))
    assert(x.lat == approx(29.8088737, rel=1e-7))

    x = gt.extrapolate(Coordinates(lon=ls2.coords[0][0], lat=ls2.coords[0][1]),24.563082409554156, radians(-98.80429346948154))
    assert(x.lon == approx(-97.1931752, rel=1e-7))
    assert(x.lat == approx(32.9859218, rel=1e-7))

    x = gt.extrapolate(Coordinates(lon=ls3.coords[0][0], lat=ls3.coords[0][1]),40.84844099617549, radians(138.95634225020362))
    assert(x.lon == approx(-94.2670405, rel=1e-7))
    assert(x.lat == approx(32.8091639, rel=1e-7))

def test_interpolate():
    c = gt.interpolate([Coordinates(*c) for c in ls4b.coords], 0.0)
    assert(c.lon == ls4b.coords[0][0])
    assert(c.lat == ls4b.coords[0][1])

    c = gt.interpolate([Coordinates(*c) for c in ls4b.coords], 243.5)
    assert(c.lon == approx(-94.87434772790684, 1e-7))
    assert(c.lat == approx(29.25999640728569, 1e-7))

    c = gt.interpolate([Coordinates(*c) for c in ls4_comb.coords], ls4a_len + ls4b_len)
    assert(c.lon == approx(ls4c.coords[0][0], rel=1e-7))
    assert(c.lat == approx(ls4c.coords[0][1], rel=1e-7))

    c = gt.interpolate([Coordinates(*c) for c in ls4_comb.coords], ls4a_len + 243.5)
    assert(c.lon == approx(-94.87434772790684, 1e-7))
    assert(c.lat == approx(29.25999640728569, 1e-7))

def test_split_line():
    first,second = gt.split_line(ls4b, 243.5)
    assert(first is not None)
    assert(second is not None)
    assert(gt.line_string_length(first) + gt.line_string_length(second) == approx(gt.line_string_length(ls4b), rel=1e-7))

    first,second = gt.split_line(ls4_comb, 243.5)
    assert(first is not None)
    assert(second is not None)
    assert(gt.line_string_length(first) + gt.line_string_length(second) == approx(gt.line_string_length(ls4_comb), rel=1e-7))

    first,second = gt.split_line(ls4_comb, 0.0)
    assert(first is None)
    assert(second is not None)
    assert(second.coords[0][0] == approx(ls4a.coords[0][0], rel=1e-7))
    assert(second.coords[0][1] == approx(ls4a.coords[0][1], rel=1e-7))

    first,second = gt.split_line(ls4_comb, gt.line_string_length(ls4a))
    assert(first is not None)
    assert(second is not None)
    assert(first.coords[-1][0] == approx(ls4b.coords[0][0], rel=1e-7))
    assert(first.coords[-1][1] == approx(ls4b.coords[0][1], rel=1e-7))
    assert(second.coords[0][0] == approx(ls4b.coords[0][0], rel=1e-7))
    assert(second.coords[0][1] == approx(ls4b.coords[0][1], rel=1e-7))

    first,second = gt.split_line(ls4_comb, gt.line_string_length(ls4a) + gt.line_string_length(ls4b))
    assert(first is not None)
    assert(second is not None)
    assert(first.coords[-1][0] == approx(ls4c.coords[0][0], rel=1e-7))
    assert(first.coords[-1][1] == approx(ls4c.coords[0][1], rel=1e-7))
    assert(second.coords[0][0] == approx(ls4c.coords[0][0], rel=1e-7))
    assert(second.coords[0][1] == approx(ls4c.coords[0][1], rel=1e-7))
"Contains a test case for WGS84 functions"

import unittest
from math import pi

from shapely.geometry import Point, LineString

from openlr import Coordinates

class GeoTests(unittest.TestCase):
    "Unit tests for all the WGS84 functions"

    geo_tool = GeoTool_4326()

    def test_distance_1(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(4.9091286, 52.3773181)
        geo2 = Coordinates(13.4622487, 52.4952885)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what google maps says (579.3 km)
        self.assertAlmostEqual(dist, 579_530, delta=3000)

    def test_distance_2(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(13.1759576, 52.4218989)
        geo2 = Coordinates(13.147999, 52.4515114)
        dist = self.geo_tool.distance(geo1, geo2)
        self.assertAlmostEqual(3800, dist, delta=10)

    def test_distance_3(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(19.3644325, 51.796037)
        geo2 = Coordinates(19.3642027, 51.7957296)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what Spatialite says
        self.assertAlmostEqual(37.7, dist, delta=0.05)

    def test_distance_4(self):
        "Compare a WGS84 distance near prime Meridian to an expected value"
        geo1 = Coordinates(-0.0000886, 51.462934)
        geo2 = Coordinates(0.000097, 51.4629935)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what Spatialite says
        self.assertAlmostEqual(14.50, dist, delta=0.05)

    def test_bearing_zero(self):
        "Test bearing function where it should be zero"
        geo1 = Coordinates(0.0, 10.0)
        geo2 = Coordinates(0.0, 20.0)
        dist = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(dist, 0.0)

    def test_bearing_180(self):
        "Test bearing function where it should be 180°"
        geo1 = Coordinates(0.0, -10.0)
        geo2 = Coordinates(0.0, -20.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, pi)

    def test_bearing_90_1(self):
        "Test bearing function where it should be 90°"
        geo1 = Coordinates(1.0, 0.0)
        geo2 = Coordinates(2.0, 0.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, pi / 2)

    def test_bearing_90_2(self):
        "Test bearing function where it should be 90°"
        geo1 = Coordinates(-1.0, 0.0)
        geo2 = Coordinates(-2.0, 0.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, -pi / 2)

    def test_projection_90(self):
        "Test point projection into 90° direction"
        geo1 = Coordinates(0.0, 0.0)
        (lon, lat) = self.geo_tool.extrapolate(geo1, 20037508.0, pi * 90.0 / 180)
        self.assertAlmostEqual(lon, 180.0, delta=0.1)
        self.assertAlmostEqual(lat, 0.0)

    def test_projection_and_angle(self):
        "Test re-projecting existing point"
        geo1 = Coordinates(13.41, 52.525)
        geo2 = Coordinates(13.414, 52.525)
        dist = self.geo_tool.distance(geo1, geo2)
        angle = self.geo_tool.bearing(geo1, geo2)
        geo3 = self.geo_tool.extrapolate(geo1, dist, angle)
        self.assertAlmostEqual(geo2.lon, geo3.lon)
        self.assertAlmostEqual(geo2.lat, geo3.lat)

    def test_point_along_path(self):
        "Test point projection along path"
        path = [
            Coordinates(0.0, 0.0),
            Coordinates(0.0, 1.0),
            Coordinates(0.0, 2.0)
        ]
        part_lengths = [self.geo_tool.distance(path[i], path[i+1]) for i in range(len(path)-1)]
        length = sum(part_lengths)
        projected = self.geo_tool.interpolate(path, 0.75 * length)
        self.assertAlmostEqual(projected.lon, 0.0, places=3)
        self.assertAlmostEqual(projected.lat, 1.5, places=3)

    def test_split_line(self):
        start = Coordinates(13.0, 52.0)
        middle = Coordinates(13.1, 52.0)
        end = Coordinates(13.1, 52.1)
        line = LineString([Point(*start), Point(*middle), Point(*end)])
        length = self.geo_tool.distance(start, middle) + self.geo_tool.distance(middle, end)
        (first, second) = self.geo_tool.split_line(line, 0.0)
        self.assertIsNone(first)
        self.assertEqual(second, line)
        (first, second) = self.geo_tool.split_line(line, 1.0 * length)
        self.assertIsNone(second)
        self.assertEqual(first, line)
        (first, second) = self.geo_tool.split_line(line, 0.5 * length)
        assert(first is not None)
        assert(second is not None)
        self.assertAlmostEqual(self.geo_tool.line_string_length(first) + self.geo_tool.line_string_length(second), self.geo_tool.line_string_length(line))
