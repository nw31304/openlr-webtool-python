"Some geo coordinates related tools"
from math import sqrt, atan2, sin, cos
from typing import Sequence, Tuple, Optional

from openlr import Coordinates
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import substring

from openlr_dereferencer.maps.abstract import GeoTool

TRAN_4326_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", allow_ballpark=False, accuracy=1.0)


class GeoTool_3857(GeoTool):

    def transform(self, lat, lon):
        return TRAN_4326_TO_3857.transform(lat, lon)

    def transform_coordinate(self, coord: Coordinates) -> Coordinates:
        """ Transforms a WGS84 coordinate into the local CRS """
        x, y = self.transform(coord.lat, coord.lon)
        return Coordinates(lon=x, lat=y)

    def distance(self, point_a: Coordinates, point_b: Coordinates) -> float:
        "Returns the distance of two local coordinates on our planet, in meters"
        return sqrt(((point_a.lon - point_b.lon) ** 2) + ((point_a.lat - point_b.lat) ** 2))

    def line_string_length(self, line_string: LineString) -> float:
        """Returns the length of a line string in meters"""
        return line_string.length

    def bearing(self, point_a: Coordinates, point_b: Coordinates) -> float:
        """Returns the angle between self and other relative to true north

        The result of this function is between -pi, pi, including them"""
        return atan2(point_b.lon - point_a.lon, point_b.lat - point_a.lat)

    def extrapolate(self, point: Coordinates, dist: float, angle: float) -> Coordinates:
        "Creates a new point that is `dist` meters away in direction `angle`"
        return Coordinates(lon=point.lon + dist * sin(angle), lat=point.lat + dist * cos(angle))

    def interpolate(self, path: Sequence[Coordinates], distance_meters: float) -> Coordinates:
        """Go `distance` meters along the `path` and return the resulting point

        When the length of the path is too short, returns its last coordinate"""

        if distance_meters <= 0:
            return Coordinates(lon=path[0][0], lat=path[0][1])

        p = LineString(path).interpolate(distance_meters, normalized=False)
        xs, ys = p.xy
        return Coordinates(lon=xs[0], lat=ys[0])

    def split_line(self, line: LineString, meters_into: float) -> Tuple[Optional[LineString], Optional[LineString]]:
        "Splits a line at `meters_into` meters and returns the two parts. A part is None if it would be a Point"
        a, b = substring(line, 0, meters_into), substring(line, meters_into, line.length)
        a = None if isinstance(a, Point) else a
        b = None if isinstance(b, Point) else b
        return (a, b)
        # if meters_into == 0.0:
        #     return (None, line)
        # else:
        #     p = line.interpolate(meters_into, normalized=False)
        #     gc = split(line, p.buffer(.001))
        #     if len(gc.geoms) > 1:
        #         return (gc.geoms[0], gc.geoms[1])
        #     else:
        #         return (gc.geoms[0], None)

    def join_lines(self, lines: Sequence[LineString]) -> LineString:
        coords = []
        last = None

        for l in lines:
            cs = l.coords
            first = cs[0]

            if last is None:
                coords.append(first)
            else:
                if first != last:
                    raise ValueError("Lines are not connected")

            coords.extend(cs[1:])
            last = cs[-1]

        return LineString(coords)
