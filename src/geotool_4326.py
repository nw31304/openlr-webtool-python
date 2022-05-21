"Some geo coordinates related tools"
from math import radians, degrees
from typing import Sequence, Tuple, Optional
from openlr import Coordinates
from shapely.geometry import LineString
from itertools import tee, accumulate
from openlr_dereferencer.maps.abstract import GeoTool
from pyproj import Geod

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    first, second = tee(iterable)
    next(second, None)
    return zip(first, second)


class GeoTool_4326(GeoTool):

    geod = Geod(ellps="WGS84")

    def transform_coordinate(self, coord: Coordinates) -> Coordinates:
        """ Transforms a WGS84 coordinate into the local CRS """
        return coord

    def distance(self, point_a: Coordinates, point_b: Coordinates) -> float:
        "Returns the distance of two WGS84 coordinates on our planet, in meters"
        _,_,dist = self.geod.inv(point_a.lon, point_a.lat, point_b.lon, point_b.lat)
        return dist

    def line_string_length(self, line_string: LineString) -> float:
        """Returns the length of a line string in meters"""
        return self.geod.geometry_length(line_string, radians=False)


    def bearing(self, point_a: Coordinates, point_b: Coordinates) -> float:
        """Returns the angle between self and other relative to true north

        The result of this function is between -pi, pi, including them"""
        r,_,_ = self.geod.inv(point_a.lon, point_a.lat, point_b.lon, point_b.lat)
        return radians(r)

    def extrapolate(self, point: Coordinates, dist: float, angle: float) -> Coordinates:
        "Creates a new point that is `dist` meters away in direction `angle` degrees"
        lon, lat,_ = self.geod.fwd(point.lon, point.lat, degrees(angle), dist)
        return Coordinates(lon=lon, lat=lat)

    def interpolate(self, path: Sequence[Coordinates], meters_into: float) -> Coordinates:
        """Go `distance` meters along the `path` and return the resulting point

        When the length of the path is too short, returns its last coordinate"""

        if meters_into == 0.0:
            return path[0]

        # one call to proj to retreive the segment lengths and forward azimuths
        lons1 = [c.lon for c in path[0:-1]]
        lats1 = [c.lat for c in path[0:-1]]
        lons2 = [c.lon for c in path[1:]]
        lats2 = [c.lat for c in path[1:]]
        fwd_azims,_,dists = self.geod.inv(lons1, lats1, lons2, lats2)

        for index,accum_distance in enumerate(accumulate(dists)):
            if accum_distance > meters_into:
                offset = dists[index] - ( accum_distance - meters_into )
                if offset == 0.0:
                    return path[index]
                else:  
                    return self.extrapolate(path[index], offset, radians(fwd_azims[index]))
        return path[-1]

    def split_line(self, line: LineString, meters_into: float) -> Tuple[Optional[LineString], Optional[LineString]]:
        "Splits a line at `meters_into` meters and returns the two parts. A part is None if it would be a Point"

        if meters_into == 0.0:
            return (None, line)

        coords = line.coords
        # one call to proj to retreive the segment lengths and forward azimuths
        lons1 = [c[0] for c in coords[0:-1]]
        lats1 = [c[1] for c in coords[0:-1]]
        lons2 = [c[0] for c in coords[1:]]
        lats2 = [c[1] for c in coords[1:]]
        fwd_azims,_,dists = self.geod.inv(lons1, lats1, lons2, lats2)

        for index,accum_distance in enumerate(accumulate(dists)):
            if accum_distance > meters_into:
                offset = dists[index] - ( accum_distance - meters_into )
                if offset == 0.0:
                    return (LineString(coords[0:index+1]), LineString(coords[index:]))
                else:  
                    c = self.extrapolate(Coordinates(lon=coords[index][0], lat=coords[index][1]), offset, radians(fwd_azims[index]))
                    return (LineString( coords[0:index+1] + [c]), LineString([c] + coords[index+1:]))

        return (line, None)

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