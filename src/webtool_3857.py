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

"""

from __future__ import annotations

from typing import Optional, cast

from openlr import Coordinates, LocationReferencePoint
from openlr import binary_decode
from psycopg2 import sql

from geotool_3857 import GeoTool_3857
from openlr_dereferencer import decode, Config
from openlr_dereferencer.decoding import MapObjects
from openlr_dereferencer.maps import MapReader
from webtool import WebToolMapReader, NODE_QUERY, LINE_QUERY, LINE_QUERY_SELECT, REV_LINE_QUERY_SELECT


class WebToolMapReader3857(WebToolMapReader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geo_tool = GeoTool_3857()
        self.find_nodes_close_to_query = sql.SQL(
            NODE_QUERY + " where geom && st_buffer(ST_GeometryFromText('SRID=3857;POINT(%s %s)'), %s)::geometry").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.nodes_table))
        self.find_lines_close_to_query = sql.SQL(f"""
            with sq as ({LINE_QUERY} where geom && st_buffer(ST_GeometryFromText('SRID=3857;POINT(%s %s)'), %s)::geometry)
                ({LINE_QUERY_SELECT} from sq where sq.flowdir in (1,3)) 
                union 
                ({REV_LINE_QUERY_SELECT} from sq where sq.flowdir in (1,2))
        """).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(self.lines_table))

    def transform_lrp(self, lrp: LocationReferencePoint) -> LocationReferencePoint:
        t_coord = self.geo_tool.transform_coordinate(Coordinates(lon=lrp.lon, lat=lrp.lat))
        return lrp._replace(lon=t_coord.lon, lat=t_coord.lat)

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
        if config is None:
            config = self.config

        ref = binary_decode(binstr)
        ref = ref._replace(points=[self.transform_lrp(lrp) for lrp in ref.points])
        if clear_cache:
            self.node_cache.clear()
            self.line_cache.clear()
        return cast(MapObjects, decode(reference=ref, reader=cast(MapReader, self), config=cast(Config, config),
                                       geo_tool=self.geo_tool))
