
from decoder_configs import StrictConfig, RelaxedConfig
from tomtom_sqlite import TomTomMapReaderSQLite
from geotool_4326 import GeoTool_4326
from openlr import Coordinates
import unittest
import logging


class TomTomSqliteTests(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        self.rdr = TomTomMapReaderSQLite(
            db_filename="/Users/dave/projects/python/openlr/data/lux-orbis.db",
            mod_spatialite="/opt/homebrew/anaconda3/envs/openlr/lib/mod_spatialite",
            lines_table="links",
            nodes_table="junctions",
            geo_tool=GeoTool_4326(),
            config=StrictConfig
        )

    def test_find_lines_close_to(self):
        coords = Coordinates(lon=6.003845930099487, lat=49.56238389015198)
        res = list(self.rdr.find_lines_close_to(coords, 30))
        assert(len(res) == 11)

    def test_find_nodes_close_to(self):
        coords = Coordinates(lon=6.003845930099487, lat=49.56238389015198)
        res = list(self.rdr.find_nodes_close_to(coords, 30))
        assert(len(res) == 5)


    def test_get_outgoing_lines(self):
        coords = Coordinates(lon=6.003845930099487, lat=49.56238389015198)
        res = list(self.rdr.find_lines_close_to(coords, 30))
        line = self.rdr.get_line("1163096179169525760")
        assert(line is not None)
        assert(line.end_node is not None)
        assert(line.start_node is not None)
        outgoing = list(line.end_node.outgoing_lines())
        assert(len(outgoing) == 2)


    def test_get_outgoing_lines2(self):
        coords = Coordinates(lon=6.003845930099487, lat=49.56238389015198)
        res = list(self.rdr.find_lines_close_to(coords, 30))
        line = self.rdr.get_line("1163096179178209280")
        assert(line is not None)
        assert(line.end_node is not None)
        assert(line.start_node is not None)
        outgoing = set(line.end_node.outgoing_lines())
        assert(len(outgoing) == 2)

    def test_match(self):
        res=self.rdr.match("CwRE+CM+jxNMHgOn+kYTHg==", RelaxedConfig)
        assert(res is not None)
        assert(len(res.lines) == 13)

    def test_match2(self):
        res=self.rdr.match("CwST9iNQMRNLQPqI87MTAg==", RelaxedConfig)
        assert(res is not None)
        assert(len(res.lines) == 23)

