from webtool.map_databases import WebToolMapReader
from openlr import Coordinates
from pytest import approx, raises
from openlr_dereferencer.decoding import LineLocation, Config
from openlr import FOW, FRC
from typing import Dict

LINES_TABLE = "lines"
NODES_TABLE = "nodes"
USER = ""
PASSWORD = ""
DBNAME = "openlr"
HOST = ""
SCHEMA = "test"
PORT = 5432

rdr = WebToolMapReader(
    lines_table = LINES_TABLE,
    nodes_table = NODES_TABLE,
    dbname = DBNAME,
    host = "",
    schema = SCHEMA,
    port = 5432
)

# Test Map    
def test_find_nodes_close_to():
    count = 0
    for n in rdr.find_nodes_close_to(Coordinates(lat=34.72685360, lon=135.57944331), 60):
        assert(n.node_id in [3406198, 3406283, 3406282, 3414366, 3426579])
        count += 1
    assert(count == 5)

def test_find_lines_close_to():
    count = 0
    for n in rdr.find_lines_close_to(Coordinates(lat=34.72685360, lon=135.57944331), 60):
        assert(n.line_id in [-5902238, -5899149, -158911, -13378116, -11568443, -8175304, -11901655, -8147599, -13398704, -5235705, -9161719, -4938508, 5902238, 5899149, 158911, 13378116, 11568443, 8175304, 11901655, 8147599, 13398704, 5235705, 9161719, 4938508])
        count += 1
    assert(count == 24)

def test_nodecount():
    assert(rdr.get_nodecount() == 5105)

def test_linecount():
    assert(rdr.get_linecount() == 7330)

def test_get_line():
    for id in [-5902238, -5899149, -158911, -13378116, -11568443, -8175304, -11901655, -8147599, -13398704, -5235705, -9161719, -4938508, 5902238, 5899149, 158911, 13378116, 11568443, 8175304, 11901655, 8147599, 13398704, 5235705, 9161719, 4938508]:
        assert(rdr.get_line(id).line_id == id)

def test_get_node():
    ns = [n.node_id for n in rdr.get_nodes()]
    for id in ns:
        assert(rdr.get_node(id).node_id == id)

def test_get_lines():
    count = 0
    for l in rdr.get_lines():
        count += 1
    assert(count == 12936)

def test_get_nodes():
    count = 0
    for l in rdr.get_nodes():
        count += 1
    assert(count == 5105)

# Test Node    
n = rdr.get_node(3406198)

def test_node_id():
    assert(n.node_id == 3406198)

def test_coordinates():
    c = n.coordinates
    assert(c.lon == approx(135.57944388509267, rel=1e-7))
    assert(c.lat == approx(34.72687194347209, rel=1e-7))

def test_incoming_lines():
    count = 0
    for l in n.incoming_lines():
        assert(l.line_id in [-8147599, -8175304, 13398704, 11901655])
        count += 1
    assert(count == 4)

def test_outgoing_lines():
    count = 0
    for l in n.outgoing_lines():
        assert(l.line_id in [8147599, 8175304, -13398704, -11901655])
        count += 1
    assert(count == 4)
    
def test_connected_lines():
    count = 0
    for l in n.connected_lines():
        assert(l.line_id in [-8147599, -8175304, 13398704, 11901655, 8147599, 8175304, -13398704, -11901655])
        count += 1
    assert(count == 8)


# Test line


def test_line_id():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    l3 = rdr.get_line(5153145)
    l4 = rdr.get_line(-5153145)

    assert(l1.line_id == 11901655)
    assert(l2.line_id == -11901655)
    assert(l3.line_id == 5153145)
    assert(l4.line_id == -5153145)

def test_start_node():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l1.start_node.node_id == 3426583)
    assert(l2.start_node.node_id == 3406198)

def test_end_node():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l2.end_node.node_id == 3426583)
    assert(l1.end_node.node_id == 3406198)

def test_fow():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l2.fow == FOW.SINGLE_CARRIAGEWAY)
    assert(l1.fow == FOW.SINGLE_CARRIAGEWAY)
    
def test_frc():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l2.frc == FRC.FRC5)
    assert(l1.frc == FRC.FRC5)

def test_geometry():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l2.geometry.geometryType() == "LineString")
    assert(l1.geometry.geometryType ()== "LineString")

def test_distance_to():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    assert(l1.distance_to(Coordinates(lon=135.578501, lat=34.727344)) == approx(58.67, rel=1e-2))
    assert(l2.distance_to(Coordinates(lon=135.578501, lat=34.727344)) == approx(58.67, rel=1e-2))

def test_length():
    l1 = rdr.get_line(11901655)
    l2 = rdr.get_line(-11901655)
    l3 = rdr.get_line(5153145)
    l4 = rdr.get_line(-5153145)
    assert(l1.length == approx(82.433, rel=1e-2))
    assert(l2.length == approx(82.433, rel=1e-2))
    assert(l3.length == approx(50.357, rel=1e-3))
    assert(l4.length == approx(50.357, rel=1e-3))

def test_match():
    rdr = WebToolMapReader(
        lines_table = LINES_TABLE,
        nodes_table = NODES_TABLE,
        dbname = DBNAME,
        host = "",
        schema = SCHEMA,
        port = 5432
    )

    with raises(Exception) as e_info:
        res = rdr.match("C2Br9xiypCOYCv1L/9kjBw==")

    my_tolerated_lfrc: Dict[ FRC, FRC ] = {
        FRC.FRC0 : FRC.FRC1,
        FRC.FRC1 : FRC.FRC3,
        FRC.FRC2 : FRC.FRC3,
        FRC.FRC3 : FRC.FRC5,
        FRC.FRC4 : FRC.FRC5,
        FRC.FRC5 : FRC.FRC7,
        FRC.FRC6 : FRC.FRC7,
        FRC.FRC7 : FRC.FRC7,
    }

    my_config = Config(
        tolerated_lfrc = my_tolerated_lfrc,
        search_radius=50,
        geo_weight = 0.66,
        frc_weight = 0.17,
        fow_weight = 0.17,
        bear_weight = 0.0
    )

    res = rdr.match("C2Br9xiypCOYCv1L/9kjBw==", config=my_config)
    assert(isinstance(res, LineLocation))
    assert(res.n_off == 0.0)
    assert(res.p_off == 0.0)
    assert([l.line_id for l in res.lines] == [-9619744,-9713879,-9125769,-5859200])
    assert(len(res.coordinates()) == 10)

def test_match_default():
    my_tolerated_lfrc: Dict[ FRC, FRC ] = {
        FRC.FRC0 : FRC.FRC1,
        FRC.FRC1 : FRC.FRC3,
        FRC.FRC2 : FRC.FRC3,
        FRC.FRC3 : FRC.FRC5,
        FRC.FRC4 : FRC.FRC5,
        FRC.FRC5 : FRC.FRC7,
        FRC.FRC6 : FRC.FRC7,
        FRC.FRC7 : FRC.FRC7,
    }

    my_config = Config(
        tolerated_lfrc = my_tolerated_lfrc,
        search_radius=50,
        geo_weight = 0.66,
        frc_weight = 0.17,
        fow_weight = 0.17,
        bear_weight = 0.0
    )

    rdr = WebToolMapReader(
        lines_table = LINES_TABLE,
        nodes_table = NODES_TABLE,
        dbname = DBNAME,
        host = "",
        schema = SCHEMA,
        port = 5432,
        config=my_config
    )

    res = rdr.match("C2Br9xiypCOYCv1L/9kjBw==", config=my_config)
    assert(isinstance(res, LineLocation))
    assert(res.n_off == 0.0)
    assert(res.p_off == 0.0)
    assert([l.line_id for l in res.lines] == [-9619744,-9713879,-9125769,-5859200])
    assert(len(res.coordinates()) == 10)
