from geotool_3857 import GeoTool_3857
from openlr import Coordinates
from pytest import approx, raises
from shapely.geometry import LineString
from math import pi, sqrt, degrees

gt = GeoTool_3857()

def test_bearing():
    origin = Coordinates(lon = 0.0, lat=0.0)
    c_1_0 = Coordinates(lon = 1.0, lat=0.0)
    c_1_1 = Coordinates(lon = 1.0, lat=1.0)
    c_0_1 = Coordinates(lon = 0.0, lat=1.0)
    c_1_neg1 = Coordinates(lon = 1.0, lat=-1.0)
    c_0_neg1 = Coordinates(lon = 0.0, lat=-1.0)
    p1 = Coordinates(lon=-10557387.386874478, lat=3412432.763758655)
    p2 = Coordinates(lon=-10557407.380536323, lat=3412432.260284689)

    assert(gt.bearing(origin, c_0_1) == approx(0, rel=1e-7))
    assert(gt.bearing(c_0_1, origin) == approx(pi, rel=1e-7))
    assert(gt.bearing(origin, c_1_0) == approx(pi/2, rel=1e-7))
    assert(gt.bearing(c_1_0, origin) == approx(-pi/2, rel=1e-7))
    assert(gt.bearing(origin, c_1_1) == approx(pi/4, rel=1e-7))
    assert(gt.bearing(c_1_1, origin) == approx(-3 * pi/4, rel=1e-7))
    assert(gt.bearing(origin, c_1_neg1) == approx(3 * pi/4, rel=1e-7))
    assert(gt.bearing(c_1_neg1, origin) == approx(-pi/4, rel=1e-7))
    assert(gt.bearing(origin, c_0_neg1) == approx(pi, rel=1e-7))
    assert(gt.bearing(c_0_neg1, origin) == approx(0, rel=1e-7))
    assert(gt.bearing(origin, origin) == approx(0, rel=1e-7))
    assert(degrees(gt.bearing(p1, p2)) % 360 == approx(270, rel=1))


def test_transform():
    wgs1 = Coordinates(lon=-95.04189848899841, lat=29.41189169883728)
    xy1 = gt.transform_coordinate(wgs1)
    assert(xy1.lon == approx(-10580015.75, rel=1e-7))
    assert(xy1.lat == approx(3428175.80, rel=1e-7))

    wgs2 = Coordinates(lon=-95.05422848899842, lat=29.42445169883728)
    xy2 = gt.transform_coordinate(wgs2)
    assert(xy2.lon == approx(-10581388.31, rel=1e-7))
    assert(xy2.lat == approx(3429780.95, rel=1e-7))

    wgs3 = Coordinates(lon=-95.06488848899842, lat=29.43528169883728)
    xy3 = gt.transform_coordinate(wgs3)
    assert(xy3.lon == approx(-10582574.98, rel=1e-7))
    assert(xy3.lat == approx(3431165.16, rel=1e-7))
    
def test_distance():
    origin = Coordinates(lon = 0.0, lat=0.0)
    c_1_0 = Coordinates(lon = 1.0, lat=0.0)
    c_1_1 = Coordinates(lon = 1.0, lat=1.0)
    c_0_1 = Coordinates(lon = 0.0, lat=1.0)
    c_1_neg1 = Coordinates(lon = 1.0, lat=-1.0)
    c_0_neg1 = Coordinates(lon = 0.0, lat=-1.0)

    assert(gt.distance(origin, c_0_1) == approx(1, rel=1e-7))
    assert(gt.distance(c_0_1, origin) == approx(1, rel=1e-7))
    assert(gt.distance(origin, c_1_0) == approx(1, rel=1e-7))
    assert(gt.distance(c_1_0, origin) == approx(1, rel=1e-7))
    assert(gt.distance(origin, c_1_1) == approx(sqrt(2), rel=1e-7))
    assert(gt.distance(c_1_1, origin) == approx(sqrt(2), rel=1e-7))
    assert(gt.distance(origin, c_1_neg1) == approx(sqrt(2), rel=1e-7))
    assert(gt.distance(c_1_neg1, origin) == approx(sqrt(2), rel=1e-7))
    assert(gt.distance(origin, c_0_neg1) == approx(1, rel=1e-7))
    assert(gt.distance(c_0_neg1, origin) == approx(1, rel=1e-7))
    assert(gt.distance(origin, origin) == approx(0, rel=1e-7))

def test_line_string_length():
    ls1 = LineString([ [0,0], [1,0], [1,1], [1,2], [2,2] ])
    ls2 = LineString([ [0,0], [1,1] ])
    ls3 = LineString([ [-5,-5], [5,5] ])
    ls = LineString(LineString([
        [-10557387.386874478,3412432.763758655],
        [-10557482.676358597,3412430.364209494],
        [-10557535.942734942,3412428.373094567],
        [-10557601.120296802,3412427.951897218],
        [-10557655.833826527,3412429.1389079643],
        [-10557711.805266498,3412431.8703094474],
        [-10557782.03673324,3412434.588947941],
        [-10557850.186525503,3412438.2010365822],
        [-10557928.31054414,3412443.8425339162],
        [-10558027.062064424,3412450.377484108],
        [-10558157.9515217,3412460.243733472],
        [-10558206.753986463,3412461.8264184115],
        [-10558261.422988392,3412464.481245194]
        ]))

    assert(gt.line_string_length(ls1) == 4.0)
    assert(gt.line_string_length(ls2) == approx(sqrt(2), rel=1e-7))
    assert(gt.line_string_length(ls3) == approx(sqrt(200), rel=1e-7))
    assert(gt.line_string_length(ls) == approx(875.2134447730233, rel=1e-7))

def test_extrapolate():
    origin = Coordinates(lon = 0.0, lat=0.0)
    c_1_0 = Coordinates(lon = 1.0, lat=0.0)
    c_1_1 = Coordinates(lon = 1.0, lat=1.0)
    c_0_1 = Coordinates(lon = 0.0, lat=1.0)
    c_1_neg1 = Coordinates(lon = 1.0, lat=-1.0)
    c_0_neg1 = Coordinates(lon = 0.0, lat=-1.0)

    c0 = gt.extrapolate(origin, 1.0, 0)
    assert( c0.lon == approx(0, rel=1e-7))
    assert( c0.lat == approx(1, rel=1e-7))
    c1 = gt.extrapolate(origin, 1.0, pi)
    assert( c1.lon == approx(0, rel=1e-7))
    assert( c1.lat == approx(-1, rel=1e-7))
    c2 = gt.extrapolate(origin, sqrt(2), pi/4)
    assert( c2.lon == approx(1, rel=1e-7))
    assert( c2.lat == approx(1, rel=1e-7))
    c3 = gt.extrapolate(origin, 1.0, pi/2)
    assert( c3.lon == approx(1, rel=1e-7))
    assert( c3.lat == approx(0, rel=1e-7))
    c4 = gt.extrapolate(origin, sqrt(2), 3*pi/4)
    assert( c4.lon == approx(1, rel=1e-7))
    assert( c4.lat == approx(-1, rel=1e-7))

def test_interpolate():
    ls1 = LineString([ [0,0], [1,0], [1,1], [1,2], [2,2] ])
    ls = LineString(LineString([
        [-10557387.386874478,3412432.763758655],
        [-10557482.676358597,3412430.364209494],
        [-10557535.942734942,3412428.373094567],
        [-10557601.120296802,3412427.951897218],
        [-10557655.833826527,3412429.1389079643],
        [-10557711.805266498,3412431.8703094474],
        [-10557782.03673324,3412434.588947941],
        [-10557850.186525503,3412438.2010365822],
        [-10557928.31054414,3412443.8425339162],
        [-10558027.062064424,3412450.377484108],
        [-10558157.9515217,3412460.243733472],
        [-10558206.753986463,3412461.8264184115],
        [-10558261.422988392,3412464.481245194]
        ]))

    c0 = gt.interpolate(ls1.coords, -1)
    assert(c0.lon == 0)
    assert(c0.lat == 0)

    c1 = gt.interpolate(ls1.coords, 0)
    assert(c1.lon == 0)
    assert(c1.lat == 0)

    c1 = gt.interpolate(ls1.coords, 1)
    assert(c1.lon == 1)
    assert(c1.lat == 0)

    c1 = gt.interpolate(ls1.coords, 2)
    assert(c1.lon == 1)
    assert(c1.lat == 1)

    c1 = gt.interpolate(ls1.coords, 3)
    assert(c1.lon == 1)
    assert(c1.lat == 2)

    c1 = gt.interpolate(ls1.coords, 4)
    assert(c1.lon == 2)
    assert(c1.lat == 2)

    c1 = gt.interpolate(ls1.coords, 5)
    assert(c1.lon == 2)
    assert(c1.lat == 2)

    c1 = gt.interpolate(ls.coords, 20)
    assert(c1.lon == approx(-10557407.380536323, rel=1e-7))
    assert(c1.lat == approx(3412432.260284689, rel=1e-7))

def test_split_line():
    ls1 = LineString([ [0,0], [1,0], [1,1], [1,2], [2,2] ])
    ls = LineString([
        [-10557387.386874478,3412432.763758655], 
        [-10557482.676358597,3412430.364209494],
        [-10557535.942734942,3412428.373094567],
        [-10557601.120296802,3412427.951897218],
        [-10557655.833826527,3412429.1389079643],
        [-10557711.805266498,3412431.8703094474],
        [-10557782.03673324,3412434.588947941],
        [-10557850.186525503,3412438.2010365822],
        [-10557928.31054414,3412443.8425339162],
        [-10558027.062064424,3412450.377484108],
        [-10558157.9515217,3412460.243733472],
        [-10558206.753986463,3412461.8264184115],
        [-10558261.422988392,3412464.481245194]
    ])
    a,b = gt.split_line(ls1, 0)
    assert(a==None)
    assert(b is not None)
    assert(b.equals(ls1))

    a,b = gt.split_line(ls1, 1)
    assert(a is not None)
    assert(b is not None)
    assert(a.equals(LineString(ls1.coords[0:2])))
    assert(b.equals(LineString(ls1.coords[1::])))

    a,b = gt.split_line(ls1, 2)
    assert(a is not None)
    assert(b is not None)
    assert(a.equals(LineString(ls1.coords[0:3])))
    assert(b.equals(LineString(ls1.coords[2::])))

    a,b = gt.split_line(ls1, 3)
    assert(a is not None)
    assert(b is not None)
    assert(a.equals(LineString(ls1.coords[0:4])))
    assert(b.equals(LineString(ls1.coords[3::])))

    a,b = gt.split_line(ls1, 4)
    assert(a is not None)
    assert(b is None)
    assert(a.equals(ls1))

    a,b = gt.split_line(ls1, 5)
    assert(a is not None)
    assert(b is None)
    assert(a.equals(ls1))

    a,b = gt.split_line(ls, 823.4346540289483)
    assert(a is not None)
    assert(b is not None)
    assert(ls.length == approx(875.2134447730233, rel=1e-7))

def test_join_lines():
    ls1 = LineString([ [0,0], [1,0], [1,1], [1,2], [2,2] ])
    ls2 = LineString([ [2,2], [3,3] ])

    ls3 = gt.join_lines([ls1,ls2])

    assert(ls3.equals(LineString([[0,0], [1,0], [1,1], [1,2], [2,2], [3,3]])))