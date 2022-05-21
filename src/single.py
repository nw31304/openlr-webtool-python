from webtool import WebToolMapReader
from webtool_4326 import WebToolMapReader4326
from openlr_dereferencer.decoding import LRDecodeError

# rdr = WebToolMapReader(host="",dbname="openlr",schema="texas",lines_table="roads",nodes_table="intersections")
rdr = WebToolMapReader4326(host="",dbname="openlr",schema="texas",lines_table="roads",nodes_table="intersections")

# rdr.match("C7yNzxTT4AEYMvTiAH4BCg==")
with open("/Users/dave/projects/python/openlr/data/texas_1000.openlrs") as in_file:
    good = 0
    bad = 0
    for code in in_file.readlines():
        try:
            rdr.match(code)
            good += 1
        except LRDecodeError:
            print(code)
            bad += 1
    print(f"{good=}; {bad=}")
