from decoder_configs import STRICT_CONFIG
#from geotool_4326 import GeoTool_4326
#from webtool_4326 import WebToolMapReader4326
from tomtom_sqlite import TomTomMapReaderSQLite

# rdr = WebToolMapReader4326(
#     host="127.0.0.1",
#     geo_tool=GeoTool_4326(),
#     port=5432,
#     user="openlr",
#     dbname="openlr_db",
#     schema="local",
#     lines_table="roads",
#     nodes_table="intersections",
#     config=STRICT_CONFIG
# )

# rdr = WebToolMapReaderSQLite(
#     db_filename="/Users/dave/projects/python/openlr/data/france.sqlite",
#     mod_spatialite="/opt/homebrew/anaconda3/envs/openlr/lib/mod_spatialite",
#     lines_table="roads",
#     nodes_table="intersections",
#     config=STRICT_CONFIG
# )

rdr = TomTomMapReaderSQLite(
    db_filename="/Users/dave/projects/python/openlr/data/france.sqlite",
    mod_spatialite="/opt/homebrew/anaconda3/envs/openlr/lib/mod_spatialite",
    lines_table="roads",
    nodes_table="intersections",
    config=STRICT_CONFIG
)
res = rdr.match("CwF+qR/ptiOfD/0uAaUjEg==")
print(res.lines)