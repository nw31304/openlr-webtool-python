"""
Implements the OpenLR python decoder protocol for a SQLite/Spatialite
DB containing the schema used by the TomTom OpenLR WebTool.

That is, lines (roads) can be two-way, as opposed to one-way only.  This
module dynamically duplicates and/or reverses roads so that the decoder
sees only one-way roads. It uses the "direction" column in the lines table
to determine whether this is necessary.

Dependencies:
    - openlr
    - openlr_dereferencer
    - pyproj
    - param

"""

from __future__ import annotations

import logging
from contextlib import closing
from itertools import chain
from math import sqrt
from sqlite3 import connect
from typing import Iterable, Optional, cast, Dict

# import param
from openlr import Coordinates, FOW
from openlr import binary_decode, FRC
from pyproj import Geod
from shapely import wkb
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

from openlr_dereferencer_python.openlr_dereferencer import decode, Config
from openlr_dereferencer_python.openlr_dereferencer.decoding import MapObjects, DEFAULT_CONFIG
from openlr_dereferencer_python.openlr_dereferencer.maps import Line as AbstractLine, Node as AbstractNode
from openlr_dereferencer_python.openlr_dereferencer.maps import MapReader
from openlr_dereferencer_python.openlr_dereferencer.maps.abstract import GeoTool

GEOD = Geod(ellps="WGS84")
SQRT_2 = sqrt(2)


class WebToolMapException(Exception):
    pass


def are_peers(candidate: Line, source: Optional[Line]) -> bool:
    """
    Returns True if candidate and source are peer lines, i.e. they are
    the same road, but in opposite directions.  This is determined
    by the line_id of the lines.

    Arguments:
        candidate:Line
            first line
        source:Optional[Line]
            second line

    Returns:
        bool
            True if candidate and source are peer lines, False otherwise
    """
    if source is None:
        return False
    else:
        return candidate.line_id == "-" + source.line_id or source.line_id == "-" + candidate.line_id


class Line(AbstractLine):
    """
    Line class implementation for the SQLite-based OpenLR webtool. Unlike
    the nodes the TTI python decoder expects, the lines in the DB can be
    bidirectional.  This class takes care of reversing and/or duplicating
    two-way roads, so they appear as one way roads to the backend matcher.  As
    this class represents reversed lines with a negation of the line_id, the
    line identifier must be integer.

    Arguments:
        map_reader:WebToolMapReader
            instance of WebToolMapReader
        line_id:int
            integer identifier of this line
        fow:FOW
            form-of-way of this line
        frc: FRC
            function road class of ths line
        length:float
            length of this line in meters
        from_int: int | Node
            either the integer identifier of this line's start point,
            or else the Node object itself
        to_int: int | Node
            either the integer identifier of this line's end point,
            or else the Node object itself
        geometry: LineString
            shapely LineString representing this line's geometry
    """

    def __init__(self, map_reader: TomTomMapReaderSQLite, line_id: str, fow: FOW, frc: FRC, length: float,
                 from_int: str | Node, to_int: str | Node, geometry: LineString):
        self.id: str = line_id
        self.map_reader: TomTomMapReaderSQLite = map_reader
        self._fow: FOW = fow
        self._frc: FRC = frc
        self._length: float = length
        self.from_int: str | Node = from_int
        self.to_int: str | Node = to_int
        self._geometry: LineString = geometry

    def __repr__(self):
        return f"Line with id={self.line_id} of length {self.length}"

    @property
    def line_id(self) -> str:
        """Returns the line id"""
        return self.id

    @property
    def start_node(self) -> "Node":
        if isinstance(self.from_int, Node):
            return self.from_int  # type:ignore
        else:
            self.from_int = self.map_reader.get_node(self.from_int)  # type:ignore
            return self.from_int

    @property
    def end_node(self) -> "Node":
        if isinstance(self.to_int, Node):
            return cast(Node, self.to_int)
        else:
            self.to_int = self.map_reader.get_node(self.to_int)
            return self.to_int

    @property
    def length(self):
        return self._length

    @property
    def frc(self):
        return self._frc

    @property
    def fow(self):
        return self._fow

    @property
    def geometry(self):
        return self._geometry

    def distance_to(self, coord) -> float:
        """Returns the distance of this line to `coord` in meters"""
        return GEOD.geometry_length(LineString(nearest_points(self._geometry, Point(coord.lon, coord.lat))))


class Node(AbstractNode):
    """
    Node class implementation for the SQLite-based OpenLR webtool.  Incoming
    and outgoing lines are cached internally once they are discovered as an
    optimization

    Arguments:
        map_reader:WebToolMapReader
            instance of WebToolMapReader
        node_id:int
            integer identifer of this node
        lon:float
            WGS84 longitude of this node's point
        lat:float
            WGS84 latitude of this node's point
    """

    def __init__(self, map_reader: TomTomMapReaderSQLite, node_id: str, lon: float, lat: float):
        self.lon = lon
        self.lat = lat
        self.map_reader = map_reader
        self.id = node_id
        self.incoming_lines_cache = []
        self.outgoing_lines_cache = []

    @property
    def node_id(self):
        return self.id

    @property
    def coordinates(self) -> Coordinates:
        return Coordinates(lon=self.lon, lat=self.lat)

    def outgoing_lines(self, source: Optional[Line] = None) -> Iterable[Line]:
        if len(self.outgoing_lines_cache) > 0:
            for line in self.outgoing_lines_cache:
                yield line
        else:
            with closing(self.map_reader.connection.cursor()) as cursor:
                # start_time = time()
                cursor.execute(self.map_reader.outgoing_lines_query, (self.node_id, self.node_id))
                # end_time = time();
                # print(f"Outgoing lines query: {end_time - start_time}")
                for (line_id, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                    line = self.map_reader.line_cache.get(line_id)
                    if line is not None and not are_peers(line, source):
                        self.outgoing_lines_cache.append(line)
                        yield line
                    else:
                        ls = LineString(wkb.loads(geom, hex=False))
                        line = Line(self.map_reader, line_id, FOW(fow), FRC(frc), length, self, to_int, ls)
                        self.map_reader.line_cache[line_id] = line
                        if not are_peers(line, source):
                            self.outgoing_lines_cache.append(line)
                            yield line

    def incoming_lines(self, source: Optional[Line] = None) -> Iterable[Line]:
        if len(self.incoming_lines_cache) > 0:
            for line in self.incoming_lines_cache:
                yield line
        else:
            with closing(self.map_reader.connection.cursor()) as cursor:
                # start_time = time()
                cursor.execute(self.map_reader.incoming_lines_query, (self.node_id, self.node_id))
                # end_time = time();
                # print(f"Incoming lines query: {end_time - start_time}")
                for (line_id, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                    line = self.map_reader.line_cache.get(line_id)
                    if line is not None and not are_peers(line, source):
                        self.incoming_lines_cache.append(line)
                        yield line
                    else:
                        ls = LineString(wkb.loads(geom, hex=False))
                        line = Line(self.map_reader, line_id, FOW(fow), FRC(frc), length, from_int, self, ls)
                        self.map_reader.line_cache[line_id] = line
                        if line is not None and not are_peers(line, source):
                            self.incoming_lines_cache.append(line)
                            yield line

    def connected_lines(self) -> Iterable[Line]:
        return chain(self.incoming_lines(), self.outgoing_lines())



class TomTomMapReaderSQLite(MapReader):
    """
    This is a reader for OpenLR webtool schema in a SQLite DB.
    It is created by the reader() method on an instance of the enclosing
    MapReaderFactory class.  Rather than passing arguments directly to the
    constructor, customization paramters are passed to the factory instance's
    constructor instead.

    Arguments:
        db_filename:str
            Filesystem path to SQLite/Spatialite DB containing
            the lines and nodes table.
            Default: ""
        mod_spatialite:str
            Spatialite extension nae appropriate for the current
            system.  This is passed directly to SQLite's
            `load_extension()` method.
            Default: "mod_spatialite"
        lines_table:str
            Table containing the lines in the map
            Default: "lines"
        nodes_table:str
            Table containing the nodes in the map
            Default: "nodes"
        config:openlr_dereferencer.Config
            A Config object containing default match parameters
            which will be used by the match() method if no config
            is supplied in the call.

    Example usage:

    >>> my_tolerated_lfrc: Dict[ FRC, FRC ] = {
        FRC.FRC0 : FRC.FRC1,
        FRC.FRC1 : FRC.FRC2,
        FRC.FRC2 : FRC.FRC3,
        FRC.FRC3 : FRC.FRC4,
        FRC.FRC4 : FRC.FRC5,
        FRC.FRC5 : FRC.FRC6,
        FRC.FRC6 : FRC.FRC7,
        FRC.FRC7 : FRC.FRC7,
        }
    >>> my_config = Config(
        tolerated_lfrc = my_tolerated_lfrc,
        max_bear_deviation = 30,
        search_radius=30,
        geo_weight = 0.66,
        frc_weight = 0.17,
        fow_weight = 0.17,
        bear_weight = 0.0
        )
    >>> rdr = TomTomMapReaderSQLite(
            db_filename="/tmp/my_db.sqlite",
            mod_spatialite="libspatialite",
            lines_table="roads",
            nodes_table="intersections"
        )
    >>> rdr.match("C2Br9xiypCOYCv1L/9kjBw==")

    """

    def __init__(self, db_filename: str, geo_tool: GeoTool, mod_spatialite: str = "mod_spatialite",
                 lines_table: str = "line", nodes_table: str = "nodes", config: Config = DEFAULT_CONFIG):

        self.db_filename = db_filename
        self.geo_tool = geo_tool
        self.mod_spatialite = mod_spatialite
        self.lines_table = lines_table
        self.nodes_table = nodes_table
        self.config = config
        self.node_cache = {}
        self.line_cache = {}
        self.line_query_select = "select id,fow,direction,frc,length,start_id as from_int,end_id as to_int,st_asbinary(geom) as geom"
        self.rev_line_query_select = "select ('-' || id),fow,direction,frc,length,end_id as from_int,start_id as to_int,st_asbinary(st_reverse(geom)) as geom"
        self.node_query_select = "select id,st_x(geom),st_y(geom)"
        self.line_query = self.line_query_select + f" from {self.lines_table}"
        self.rev_line_query = self.rev_line_query_select + f" from {self.lines_table}"
        self.node_query = self.node_query_select + f" from {self.nodes_table}"
        self.get_line_query = self.line_query + " where id=?"
        self.get_lines_query = self.line_query + " union " + self.rev_line_query + " where direction = 1"
        self.get_linecount_query = f"select count(1) from {self.lines_table}"
        self.get_node_query = self.node_query + " where id=?"
        self.get_nodes_query = self.node_query
        self.get_nodecount_query = f"select count(1) from {self.nodes_table}"
        self.find_nodes_close_to_query = f"""
        with tgt as (select makepoint(?,?,4326) as p)
        {self.node_query}
        where
            rowid in ( SELECT ROWID FROM SpatialIndex WHERE f_table_name= "{self.nodes_table}"  AND search_frame=buildmbr(?,?,?,?,4326))
        and
            distance(geom,(select p from tgt),1) <= ?
        """
        self.find_lines_close_to_query = f"""
        with tgt as (select makepoint(?,?,4326) as p),
            candidates as (
                select * from '{self.lines_table}' r
                where
                    rowid in ( SELECT ROWID FROM SpatialIndex WHERE f_table_name= "{self.lines_table}"  AND search_frame=buildmbr(?,?,?,?,4326))
                and
                    distance(r.geom,(select p from tgt),1) <= ?
            )
        {self.line_query_select} from candidates c
        union 
        {self.rev_line_query_select} from candidates c where c.direction = 1
        """
        self.outgoing_lines_query = self.line_query + " where from_int = ? union " + self.rev_line_query + " where from_int = ? and direction = 1"
        self.incoming_lines_query = self.line_query + " where to_int = ? union " + self.rev_line_query + " where to_int = ? and direction = 1"

        self.connection = connect(f"file:{self.db_filename}?mode=ro", uri=True)
        self.connection.enable_load_extension(True)
        _ = self.connection.execute(f"""select load_extension("{self.mod_spatialite}")""").fetchall()

    def get_map_bounds(self) -> Polygon:
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(f"select st_asbinary(extent(geom)) from {self.lines_table}")
            (bounds,) = cursor.fetchone()
            return wkb.loads(bounds, hex=False)

    def match(self, binstr: str, clear_cache: bool = True, config: Optional[Config] = None) -> Optional[MapObjects]:
        """
        Decode an OpenLR binary string

        Arguments:
            binstr:str
                binary-encoded OpenLR string (i.e. "C7xSuRUHaAEcKfncBo4BKx8=")
            clear_cache:bool
                whether to clear the internal line and node cache before matching
                Default: True
            config:Optional[Config]
                configuration object which overrides instance level config
                Default: None

        Returns:
            A registered subtype of MapObjects( currently Coordinates, LineLocation,
            PointAlongLine, or PoiWithAccessPoint)

        Raises:
            LRDecodeError:
                Raised if the decoding process was not successful.
        """
        if config is None:
            config = self.config

        ref = binary_decode(binstr)
        if clear_cache:
            self.node_cache.clear()
            self.line_cache.clear()
        try:
            return cast(MapObjects,
                        decode(reference=ref, reader=cast(MapReader, self), config=cast(Config, config),
                               geo_tool=self.geo_tool))
        except Exception as e:
            logging.info(f"Error during decode of {ref}: {e}")
            return None

    def get_line(self, line_id: str) -> Line:
        # Just verify that this line ID exists.
        line = self.line_cache.get(line_id)
        if line is not None:
            return line
        raise WebToolMapException(f"Line {line_id} should have been in the cache but was not found")

    def get_lines(self) -> Iterable[Line]:
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.get_lines_query)
            # end_time = time();
            # print(f"get_lines query: {end_time - start_time}")
            for (line_id, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                line = self.line_cache.get(line_id)
                if line is not None:
                    yield line
                else:
                    ls = LineString(wkb.loads(geom, hex=False))
                    line = Line(self, line_id, FOW(fow), FRC(frc), length, from_int, to_int, ls)
                    self.line_cache[line_id] = line
                    yield line

    def get_linecount(self) -> int:
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.get_linecount_query)
            # end_time = time();
            # print(f"Get linecount query: {end_time - start_time}")
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException("Error retrieving line count from datastore")
            (count,) = res
            return count

    def get_node(self, node_id: str) -> Node:
        n = self.node_cache.get(node_id)
        if n is not None:
            return n
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.get_node_query, (node_id,))
            # end_time = time();
            # print(f"Get node query: {end_time - start_time}")
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException(f"Error retrieving node {node_id} from datastore")
            (node_id, lon, lat) = res
            n = Node(self, node_id, lon, lat)
            self.node_cache[node_id] = n
            return n

    def get_nodes(self) -> Iterable[Node]:
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.get_nodes_query)
            # end_time = time();
            # print(f"Get nodes query: {end_time - start_time}")
            for (node_id, lon, lat) in cursor:
                n = self.node_cache.get(node_id)
                if n is not None:
                    yield n
                else:
                    n = Node(self, node_id, lon, lat)
                    self.node_cache[node_id] = n
                    yield n

    def get_nodecount(self) -> int:
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.get_nodecount_query)
            # end_time = time();
            # print(f"Get nodecount query: {end_time - start_time}")
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException("Error retrieving node count from datastore")
            (count,) = res
            return count

    def find_nodes_close_to(self, coord: Coordinates, dist: float) -> Iterable[Node]:
        """Finds all nodes in a given radius, given in meters
        Yields every node within this distance to `coord`."""
        lon, lat = coord.lon, coord.lat
        r = dist * SQRT_2
        lons, lats, _ = GEOD.fwd(lons=[lon, lon], lats=[lat, lat], az=[225, 45], dist=[r, r], radians=False)
        with closing(self.connection.cursor()) as cursor:
            # start_time = time()
            cursor.execute(self.find_nodes_close_to_query, (lon, lat, lons[0], lats[0], lons[1], lats[1], dist))
            # end_time = time();
            # print(f"find_nodes_close_to query: {end_time - start_time}")
            # nodes = cursor.fetchall()
            for (node_id, lon, lat) in cursor:
                n = self.node_cache.get(node_id)
                if n is not None:
                    yield n
                else:
                    n = Node(self, node_id, lon, lat)
                    self.node_cache[node_id] = n
                    yield n

    def find_lines_close_to(self, coord: Coordinates, dist: float) -> Iterable[Line]:
        """Yields all lines within `dist` meters around `coord`"""
        lon, lat = coord.lon, coord.lat
        r = dist * SQRT_2
        lons, lats, _ = GEOD.fwd(lons=[lon, lon], lats=[lat, lat], az=[225, 45], dist=[r, r], radians=False)
        with closing(self.connection.cursor()) as cursor:
            # start_time=time()
            cursor.execute(self.find_lines_close_to_query, (lon, lat, lons[0], lats[0], lons[1], lats[1], dist))
            # end_time = time();
            # print(f"find_lines_close_to query: {end_time - start_time}")
            for (line_id, fow, _, frc, length, from_int, to_int, geom) in cursor:
                line = self.line_cache.get(line_id)
                if line is not None:
                    yield line
                else:
                    ls = LineString(wkb.loads(geom, hex=False))
                    line = Line(self, line_id, FOW(fow), FRC(frc), length, from_int, to_int, ls)
                    self.line_cache[line_id] = line
                    yield line
