"""
Implements the OpenLR python decoder protocol for a PostgreSQL/PostGIS
DB containing the schema used by the TomTom OpenLR WebTool.

That is, lines (roads) can be two-way, as opposed to one-way only.  This
module dynamically duplicates and/or reverses roads so that the decoder
sees only one-way roads. It uses the "flowdir" column in the lines table
to determine whether this is necessary.

Dependencies:
    - openlr
    - openlr-dereferencer
    - pyproj
    - psycopg2
    - param

"""

from __future__ import annotations
import psycopg2 as pg
from psycopg2 import sql
from typing import Iterable, Optional, cast
from openlr import Coordinates, FRC, FOW
from openlr_dereferencer.maps import MapReader
from openlr_dereferencer import decode, Config
from openlr_dereferencer.decoding import MapObjects, DEFAULT_CONFIG
import param
from itertools import chain
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
from shapely import wkb
from openlr_dereferencer.maps import Line as AbstractLine, Node as AbstractNode
from pyproj import Geod
from openlr import binary_decode, FRC

GEOD = Geod(ellps="WGS84")

LINE_QUERY_SELECT = "select id,meta,fow,flowdir,frc,len,from_int,to_int,geom"
REV_LINE_QUERY_SELECT = "select -id,meta,fow,flowdir,frc,len,to_int as from_int,from_int as to_int,st_reverse(geom)"
NODE_QUERY_SELECT = "select id,st_x(geom),st_y(geom)"
LINE_QUERY = LINE_QUERY_SELECT + " from {schema}.{table}"
REV_LINE_QUERY = REV_LINE_QUERY_SELECT + " from {schema}.{table}"
NODE_QUERY = NODE_QUERY_SELECT + " from {schema}.{table}"


class WebToolMapException(Exception):
    pass


class Line(AbstractLine):
    """
    Line class implementation for the PostgreSQL-based OpenLR webtool. Unlike
    the nodes the TTI python decoder expects, the lines in the DB can be
    bidirectional.  This class takes care of reversing and/or duplicating 
    two-way roads so they appear as one way roads to the backend matcher.  As
    this class represents reversed lines with a negation of the the line_id, the
    line identifier must be integer.

    Arguments:
        map_reader:WebToolMapReader
            instance of WebToolMapReader
        line_id:int
            integer identifier of this line
        meta:str
            arbitrary string metadata used to identify this line in
            customer's datastore
        fow:FOW
            form-of-way of this line
        frc: FRC
            function road class of ths line
        length:float
            length of this line in meters
        from_int: int | Node
            either the integer idetifier of this line's start point,
            or else the Node object itself
        to_int: int | Node
            either the integer idetifier of this line's end point,
            or else the Node object itself
        geometry: LineString
            shapely LineString representing this line's geometry
    """

    def __init__(self, map_reader: WebToolMapReader, line_id: int, meta: str, fow: FOW, frc: FRC, length: float, from_int: int | Node, to_int: int | Node, geometry: LineString):
        self.id = line_id
        self._meta = meta
        self.map_reader = map_reader
        self._fow: FOW = fow
        self._frc: FRC = frc
        self._length: float = length
        self.from_int: int | Node = from_int
        self.to_int: int | Node = to_int
        self._geometry: LineString = geometry

    def __repr__(self):
        return f"Line with id={self.line_id} of length {self.length}"

    @property
    def line_id(self) -> int:
        "Returns the line id"
        return self.id

    @property
    def meta(self) -> str:
        "Returns the metadata"
        return self._meta

    @property
    def start_node(self) -> "Node":
        if type(self.from_int) == Node:
            return(self.from_int)  # type:ignore
        else:
            self.from_int = self.map_reader.get_node(
                self.from_int)  # type:ignore
            return(self.from_int)

    @property
    def end_node(self) -> "Node":
        if type(self.to_int) == Node:
            return(cast(Node, self.to_int))
        else:
            self.to_int = self.map_reader.get_node(cast(int, self.to_int))
            return(self.to_int)

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
        "Returns the distance of this line to `coord` in meters"
        return GEOD.geometry_length(LineString(nearest_points(self._geometry, Point(coord.lon, coord.lat))))


class Node(AbstractNode):
    """
    Node class implementation for the PostgreSQL-based OpenLR webtool.  Incoming
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

    def __init__(self, map_reader: WebToolMapReader, node_id: int, lon: float, lat: float):
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

    def outgoing_lines(self) -> Iterable[Line]:
        if len(self.outgoing_lines_cache) > 0:
            for line in self.outgoing_lines_cache:
                yield line
        else:
            with self.map_reader.connection.cursor() as cursor:
                cursor.execute(self.map_reader.outgoing_lines_query,
                               (self.node_id, self.node_id))
                for (line_id, meta, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                    l = self.map_reader.line_cache.get(line_id)
                    if l is not None:
                        self.outgoing_lines_cache.append(l)
                        yield l
                    else:
                        ls = LineString(wkb.loads(geom, hex=True))
                        l = Line(self.map_reader, line_id, meta, FOW(
                            fow), FRC(frc), length, self, to_int, ls)
                        self.map_reader.line_cache[line_id] = l
                        self.outgoing_lines_cache.append(l)
                        yield l

    def incoming_lines(self) -> Iterable[Line]:
        if len(self.incoming_lines_cache) > 0:
            for line in self.incoming_lines_cache:
                yield line
        else:
            with self.map_reader.connection.cursor() as cursor:
                cursor.execute(self.map_reader.incoming_lines_query,
                               (self.node_id, self.node_id))
                for (line_id, meta, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                    l = self.map_reader.line_cache.get(line_id)
                    if l is not None:
                        self.incoming_lines_cache.append(l)
                        yield l
                    else:
                        ls = LineString(wkb.loads(geom, hex=True))
                        l = Line(self.map_reader, line_id, meta, FOW(
                            fow), FRC(frc), length, from_int, self, ls)
                        self.map_reader.line_cache[line_id] = l
                        self.incoming_lines_cache.append(l)
                        yield l

    def connected_lines(self) -> Iterable[Line]:
        return chain(self.incoming_lines(), self.outgoing_lines())


@MapReader.register
class WebToolMapReader(param.Parameterized):
    """
    This is a reader for OpenLR webtool schema in a PostgreSQL DB.
    It is created by the reader() method on an instance of the enclosing 
    MapReaderFactory class.  Rather than passing arguments directly to the
    constructor, customization paramters are passed to the factory instance's
    constructor instead.

    Arguments:
        host:str
            Hostname of the PostgreSQL server
            Default: "127.0.0.1"
        port:int
            Port which the PG cluster is listening on.  
            Default: 5432
        user:str
            PG user name
            Default: ""
        password:str
            Password for `user`
            Default: ""
        dbname:str
            PG database constaining `lines` and `nodes` tables
            Default: "openlr"
        schema::str
            DB schema containing `lines` and `nodes` tables
            Default: "local"
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
    >>> rdr = WebToolMapReader(
            host="192.168.1.10",
            port=5432,
            user="openlr",
            password="openlrwpd",
            dbname="openlr",
            schema="local",
            config=myconfig
            )
    >>> rdr.match("C2Br9xiypCOYCv1L/9kjBw==")

    """
    # connection parameters
    host = param.String(default="")
    port = param.Integer(bounds=(1024, None), default=5432)
    user = param.String(default="")
    password = param.String(default="")
    dbname = param.String(default="openlr")

    # tables
    schema = param.String(default="local")
    lines_table = param.String(default="lines")
    nodes_table = param.String(default="nodes")

    # default match config
    config = param.ClassSelector(class_=Config, default=DEFAULT_CONFIG)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.node_cache = {}
        self.line_cache = {}
        self.get_line_query = sql.SQL(LINE_QUERY + " where id=%s").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.lines_table))
        self.get_lines_query = sql.SQL(LINE_QUERY + " where flowdir in (1,3) union " + REV_LINE_QUERY + " where flowdir in (1,2)").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.lines_table))
        self.get_linecount_query = sql.SQL("select count(1) from {schema}.{table}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.lines_table))
        self.get_node_query = sql.SQL(NODE_QUERY + " where id=%s").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.nodes_table))
        self.get_nodes_query = sql.SQL(NODE_QUERY).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.nodes_table))
        self.get_nodecount_query = sql.SQL("select count(1) from {schema}.{table}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.nodes_table))
        self.find_nodes_close_to_query = sql.SQL(NODE_QUERY + " where geom && st_buffer(ST_GeographyFromText('SRID=4326;POINT(%s %s)'), %s)::geometry").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.nodes_table))
        self.find_lines_close_to_query = sql.SQL(f"""
            with sq as ({LINE_QUERY} where geom && st_buffer(ST_GeographyFromText('SRID=4326;POINT(%s %s)'), %s)::geometry)
                ({LINE_QUERY_SELECT} from sq where sq.flowdir in (1,3)) 
                union 
                ({REV_LINE_QUERY_SELECT} from sq where sq.flowdir in (1,2))
        """).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.lines_table))
        self.outgoing_lines_query = sql.SQL(LINE_QUERY + " where from_int = %s and flowdir in (1,3) union " + REV_LINE_QUERY + " where to_int = %s and flowdir in (1,2)").format(
            table=sql.Identifier(self.lines_table),
            schema=sql.Identifier(self.schema))
        self.incoming_lines_query = sql.SQL(LINE_QUERY + " where to_int = %s and flowdir in (1,3) union " + REV_LINE_QUERY + " where from_int = %s and flowdir in (1,2)").format(
            table=sql.Identifier(self.lines_table),
            schema=sql.Identifier(self.schema))

        self.connection = pg.connect(
            host=self.host, port=self.port, user=self.user, password=self.password, dbname=self.dbname)

    def match(self, binstr: str, clear_cache: bool = True, config: Optional[Config] = None) -> MapObjects:
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
        if config == None:
            config = self.config

        ref = binary_decode(binstr)
        if clear_cache:
            self.node_cache.clear()
            self.line_cache.clear()
        return cast(MapObjects, decode(reference=ref, reader=cast(MapReader, self), config=cast(Config, config)))

    def get_line(self, line_id: int) -> Line:
        # Just verify that this line ID exists.
        l = self.line_cache.get(line_id)
        if l is not None:
            return(l)
        raise WebToolMapException(
            f"Line {line_id} should have been in the cache but was not found")

    def get_lines(self) -> Iterable[Line]:
        with self.connection.cursor() as cursor:
            cursor.execute(self.get_lines_query)
            for (line_id, meta, fow, flowdir, frc, length, from_int, to_int, geom) in cursor:
                l = self.line_cache.get(line_id)
                if l is not None:
                    yield l
                else:
                    ls = LineString(wkb.loads(geom, hex=True))
                    l = Line(self, line_id, meta, FOW(fow), FRC(
                        frc), length, from_int, to_int, ls)
                    self.line_cache[line_id] = l
                    yield l

    def get_linecount(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(self.get_linecount_query)
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException(
                    "Error retrieving line count from datastore")
            (count,) = res
            return count

    def get_node(self, node_id: int) -> Node:
        n = self.node_cache.get(node_id)
        if n is not None:
            return n
        with self.connection.cursor() as cursor:
            cursor.execute(self.get_node_query, (node_id,))
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException(
                    f"Error retrieving node {node_id} from datastore")
            (node_id, lon, lat) = res
            n = Node(self, node_id, lon, lat)
            self.node_cache[node_id] = n
            return n

    def get_nodes(self) -> Iterable[Node]:
        with self.connection.cursor() as cursor:
            cursor.execute(self.get_nodes_query)
            for (node_id, lon, lat) in cursor:
                n = self.node_cache.get(node_id)
                if n is not None:
                    yield n
                else:
                    n = Node(self, node_id, lon, lat)
                    self.node_cache[node_id] = n
                    yield n

    def get_nodecount(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(self.get_nodecount_query)
            res = cursor.fetchone()
            if res is None:
                raise WebToolMapException(
                    f"Error retrieving node count from datastore")
            (count,) = res
            return count

    def find_nodes_close_to(self, coord: Coordinates, dist: float) -> Iterable[Node]:
        """Finds all nodes in a given radius, given in meters
        Yields every node within this distance to `coord`."""
        lon, lat = coord.lon, coord.lat
        with self.connection.cursor() as cursor:
            cursor.execute(self.find_nodes_close_to_query, (lon, lat, dist))
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
        "Yields all lines within `dist` meters around `coord`"
        lon, lat = coord.lon, coord.lat
        with self.connection.cursor() as cursor:
            cursor.execute(self.find_lines_close_to_query, (lon, lat, dist))
            for (line_id, meta, fow, _, frc, length, from_int, to_int, geom) in cursor:
                l = self.line_cache.get(line_id)
                if l is not None:
                    yield l
                else:
                    ls = LineString(wkb.loads(geom, hex=True))
                    l = Line(self, line_id, meta, FOW(fow), FRC(
                        frc), length, from_int, to_int, ls)
                    self.line_cache[line_id] = l
                    yield l
