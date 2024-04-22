from map_databases.tomtom_sqlite import TomTomMapReaderSQLite
from decoder_configs import StrictConfig
from webtool.geotools.geotool_4326 import GeoTool_4326

rdr = TomTomMapReaderSQLite(
    db_filename="/Users/dave/projects/python/openlr/data/hris/umd-mnr.db",
    mod_spatialite="/opt/homebrew/anaconda3/envs/openlr/lib/mod_spatialite",
    lines_table="links",
    nodes_table="junctions",
    geo_tool=GeoTool_4326(),
    config=StrictConfig
)
res = rdr.match("C8l2sxv7NBpjDALbAXQaFQ==")
print(res.lines)