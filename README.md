# openlr-webtool-python
## Overview
Implements the OpenLR python decoder protocol for a PostgreSQL/PostGIS
DB containing the schema used by the TomTom OpenLR WebTool.  That is, 
lines (roads) can be two-way, as opposed to one-way only, and a `meta` 
column links the map entries to map elements in a separate datastore.  This
module dynamically duplicates and/or reverses roads so that the decoder
sees only one-way roads. It uses the `flowdir` column in the lines table
to determine whether this is necessary.

This code is a wrapper around the [TomTom Python OpenLR decoder implementation](https://github.com/tomtom-international/openlr-dereferencer-python).  For more information about OpenLR, please see the [OpenLR Whitepaper](https://www.openlr-association.com/fileadmin/user_upload/openlr-whitepaper_v1.5.pdf).

## DB schema 
The PostgreSQL / PostGIS DB must contain tables representing lines (road segments) and nodes (intersections).  The schema for these tables is the same as is recognized by the OpenLR WebTool Docker utility, and is described below.  

### Lines table schema
| Column    |           Type            | Comments               |
| --------- |:--------------------------|:-----------------------|
|  id       | bigint                    | Unique primary key     |
|  meta     | text                      | Arbitrary string       |
|  fow      | smallint                  | [Form of Way](https://www.openlr-association.com/fileadmin/user_upload/openlr-whitepaper_v1.5.pdf#page=32) |
|  frc      | smallint                  | [Functional Road Class](https://www.openlr-association.com/fileadmin/user_upload/openlr-whitepaper_v1.5.pdf#page=31)  |
|  flowdir  | smallint                  | Traffic flow direction |
|  from_int | bigint                    | Start node ID          |
|  to_int   | bigint                    | End node ID            | 
|  len      | double precision          | Line length in meters  |
|  geom     | geometry(LineString,4326) | PostGIS LineString     | 


### Nodes table schema
| Column    |           Type            | Comments               |
| --------- |:--------------------------|:-----------------------|
|  id       | bigint                    | Unique primary key     |
|  geom     | geometry(Point,4326)      | PostGIS Point geometry | 

### Notes
- The line table `meta` field can be an arbitrary string, and is used to correlate roads elements in the lines table to the corresponding elements in the target map
- `flowdir` column definition:
    - 1: traffic flow is bidirectional
    - 2:  traffic flow is one way, from digitization end to digitization start ( S <- E ) )
    - 3:  traffic flow is one way, from digitization start to digitization end ( S -> E ) )
- `from_int` and `to_int` are foreign key references to the `id` column of the `nodes` table 

## Sample usage:
```python
from openlr import FRC, FOW
from webtool import WebToolMapReader
from typing import Dict
from openlr_dereferencer import Config

my_tolerated_lfrc: Dict[ FRC, FRC ] = {
    FRC.FRC0 : FRC.FRC1,
    FRC.FRC1 : FRC.FRC2,
    FRC.FRC2 : FRC.FRC3,
    FRC.FRC3 : FRC.FRC4,
    FRC.FRC4 : FRC.FRC5,
    FRC.FRC5 : FRC.FRC6,
    FRC.FRC6 : FRC.FRC7,
    FRC.FRC7 : FRC.FRC7,
}

my_config = Config(
    tolerated_lfrc = my_tolerated_lfrc,
    max_bear_deviation = 30,
    search_radius=30,
    geo_weight = 0.66,
    frc_weight = 0.17,
    fow_weight = 0.17,
    bear_weight = 0.0
)
   
  rdr = WebToolMapReader(
    host="",
    port=5432,
    user="",
    password="",
    dbname="test_db",
    schema="sample",
    lines_table="roads",
    nodes_table="intersections",
    config=my_config
  )

res=rdr.match("C7yP6xTT6QEWE/t6/+0BCA==")
    # Out[11]: <openlr_dereferencer.decoding.line_location.LineLocation at 0x7fae582721c0>
res.lines
    #Out[14]:
    #[Line with id=3736240 of length 14.658514187337138,
    # Line with id=2487940 of length 271.09294979343383,
    # Line with id=1531179 of length 114.98001126157855,
    # Line with id=2564465 of length 762.4772421777637]

len(res.coordinates())
    # Out[16]: 22

res.n_off
    #Out[20]: 45.791227508416654

res.p_off
    # Out[21]: 0.0

```

## Batch decoder utility
The `batch_match.py` utility can bulk-match a file containing binary openlr codes and 
write the results to a tab separated CSV file.  See comments in the file for more details.

## Dependencies:
    - python >= 3.7
    - openlr >= 1.0.1
    - openlr-dereferencer >= 1.2.0
    - pyproj >= 2.6.1
    - psycopg2 >= 2.8.6
    - param >= 1.12.0
## Optional dependencies
    - pytest >= 3.5.0 (to run unit tests)
    - folium >= 0.12.1
    - panel >= 0.12.6
    - ipywidgets >= 7.7.0

## Mac silicon notes
  // libspatialite v5.1.0 is here:
  $ export DYLD_LIBRARY_PATH=/opt/homebrew/lib
  $ ls -la /opt/homebrew/lib/mod_spatialite.dylib
  lrwxr-xr-x  1 dave  admin  54 30 Sep 13:28 /opt/homebrew/lib/mod_spatialite.dylib -> ../Cellar/libspatialite/5.1.0/lib/mod_spatialite.dylib
  
  // and also here, built from source:
  $ ls -la /usr/local/lib/mod_spatialite.dylib
  lrwxr-xr-x  1 root  wheel  22  1 Oct 12:58 /usr/local/lib/mod_spatialite.dylib -> mod_spatialite.8.dylib

  zsh ❯ /usr/local/bin/sqlite3 /Users/dave/projects/python/openlr/data/france.sqlite
  SQLite version 3.40.0 2022-08-12 18:46:01
  Enter ".help" for usage hints.
  sqlite> .headers on
  sqlite> .mode column
  sqlite> SELECT load_extension('/usr/local/lib/mod_spatialite');
