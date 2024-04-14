"""
Implements the OpenLR python decoder protocol for a PostgreSQL/PostGIS
DB containing the schema used by the TomTom OpenLR WebTool.

That is, lines (roads) can be two-way, as opposed to one-way only.  This
module dynamically duplicates and/or reverses roads so that the decoder
sees only one-way roads. It uses the "flowdir" column in the lines table
to determine whether this is necessary.

Dependencies:
    - openlr
    - openlr-dereferencer (with GeoTool modifications)
    - pyproj
    - psycopg2-binary

"""

from __future__ import annotations
from typing import Optional, cast
from openlr import binary_decode
from geotools.geotool_4326 import GeoTool_4326
from openlr_dereferencer_python.openlr_dereferencer import decode, Config
from openlr_dereferencer_python.openlr_dereferencer.decoding import MapObjects
from openlr_dereferencer_python.openlr_dereferencer.maps import MapReader
from webtool import WebToolMapReader


class WebToolMapReader4326(WebToolMapReader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geo_tool = GeoTool_4326()

    def match(self, binstr: str, clear_cache: bool = True, config: Optional[Config] = None) -> MapObjects:
        if config is None:
            config = self.config

        ref = binary_decode(binstr)
        if clear_cache:
            self.node_cache.clear()
            self.line_cache.clear()
        return cast(MapObjects, decode(reference=ref, reader=cast(MapReader, self), config=cast(Config, config),
                                       geo_tool=self.geo_tool))
