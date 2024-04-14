"""
    Match a file containing binary openlr codes and 
    write the results to a tab separated CSV file
"""

import logging
import multiprocessing as mp
import timeit
from multiprocessing import Queue, cpu_count
from typing import List, cast

from decoder_configs import StrictConfig, RelaxedConfig
from geotools.geotool_4326 import GeoTool_4326
from openlr_dereferencer_python.openlr_dereferencer.decoding import LineLocation, MapObjects, PointAlongLine, Coordinates
from map_databases.webtool_sqlite import WebToolMapReaderSQLite, Line

logging.basicConfig(level=logging.WARNING)

# number of concurrent decoder worker processes
WORKER_COUNT = cpu_count() - 1
# name of PG table containing the lines in the network
LINES_TABLE = "roads"
# name of PG table containing the nodes in the network
NODES_TABLE = "intersections"
# Postgres user
USER = ""
# Postgres password
PASSWORD = ""
# Database containing the lines and nodes
DBNAME = "openlr"
# Postgres host name
HOST = ""
# Schema containing the lines and nodes table
SCHEMA = "texas"
# PostgreSQL port
PORT = 5432

# Special purpose queue message
POISON_PILL_MSG="__DONE__"
FAILED_DECODING_MSG="__FAILED__"

# File containing binary-encoded openlr codes to be matched.
# One per line, lines terminated by line feeds
CODES_FN = "/Users/dave/projects/python/openlr/data/france.overture.openlrs"

# Tab separated CSV to be created with decoding results. Fields are:
# code \t points \t [meta, dir] \t n_off \t p_off
#OUTPUT_FN = "/Users/dave/projects/python/openlr/data/france.decoded"
OUTPUT_FN = "/dev/null"


def load_queue(q):
    """
        This loader process reads a file containing the openlr codes to be decoded and places each code on
        the worker input queue.  At EOF, it inserts WORKER_COUNT "poison pills" into the queue so 
        that each worker receives one and shuts itself down
    """
    with open(CODES_FN, "r") as infile:
        for line in infile.readlines():
            q.put(line.rstrip())
    for _ in range(WORKER_COUNT):
        q.put(POISON_PILL_MSG)


def worker(id: int, q_in: Queue, q_out: Queue):
    """
        Each worker takes a record off the queue and attempts to decode it.  If it successful, it places a tuple
        containing the code as well as the decoded coordinates on the writer input queue.  If it is unsuccessful,
        it places a FAILED_DECODING_MSG message on the writer's queue.  WHen it sees a poison pill message, it 
        places a POISON_PILL_MSG message on the writer queue and terminates.
    """

    def enqueue(r: MapObjects) -> None:
        data = ()

        if isinstance(result, LineLocation):
            data = (
                code,
                repr([(c.lon, c.lat) for c in result.coordinates()]),
                repr([(l.meta, l.line_id > 0)
                     for l in cast(List[Line], result.lines)]),
                result.p_off,
                result.n_off
            )
        elif isinstance(result, PointAlongLine):
            lon, lat = result.coordinates()
            data = (
                code,
                repr([(lon, lat)]),
                repr([cast(Line, result.line)]),
                result.positive_offset,
                0.0
            )
        elif isinstance(result, Coordinates):
            lon, lat = result
            data = (
                code,
                repr([(lon, lat)]),
                repr([]),
                0.0,
                0.0
            )
        else:
            logging.warning(
                "Unexpected map object type: {} returned from decode.  Only (LineLocations, PointALongLine, "
                "Coordinates) currently supported", type(result))
            return

        q_out.put(data)

    rdr = WebToolMapReaderSQLite(
        db_filename="/Users/dave/projects/python/openlr/data/france.sqlite",
        geo_tool=GeoTool_4326(),
        #spatialite_target="/Users/dave/opt/anaconda3/envs/openlr-3.10/lib/mod_spatialite",
        #spatialite_target="/opt/homebrew/anaconda3/envs/openlr/lib/mod_spatialite",
        mod_spatialite="/usr/local/lib/mod_spatialite",
        lines_table="roads",
        nodes_table="intersections",
        config=StrictConfig
    )
    # rdr = WebToolMapReader(
    #     lines_table=LINES_TABLE,
    #     nodes_table=NODES_TABLE,
    #     user=USER,
    #     password=PASSWORD,
    #     dbname=DBNAME,
    #     host=HOST,
    #     schema=SCHEMA,
    #     port=PORT,
    #     config=STRICT_CONFIG
    # )

    logging.info(f"Worker {id} initialized")
    code = q_in.get()

    while code != POISON_PILL_MSG:
        try:
            result = rdr.match(code)
            enqueue(result)
        except:
            try:
                result = rdr.match(code, config=RelaxedConfig)
                enqueue(result)
            except:
                q_out.put((FAILED_DECODING_MSG, None, None, None, None))
        code = q_in.get()
    q_out.put((code, None, None, None, None))
    logging.info(f"Worker {id} shutting down")


def print_progress(successes, fails, start_time):
    """
        Prints a progress message    
    """
    current_time = timeit.default_timer()
    elapsed = current_time - start_time
    attempts = successes + fails
    print(f"Attempts: {attempts}; Successes: {successes}; Failures: {fails}; Success rate: {100 * (successes/attempts):.2f}%;  Match rate:  ({(attempts / elapsed):.02f} codes/sec)", end='\r')


if __name__ == '__main__':
    workers = []
    ctx = mp.get_context('spawn')
    # create the worker and writer queues
    q_in = ctx.Queue(0)
    q_out = ctx.Queue(0)

    # spawn the loader, passing it the worker queue to fill
    loader = ctx.Process(target=load_queue, args=(q_in,))
    loader.start()
    active_workers = 0
    responses_received = 0
    start_time = timeit.default_timer()

    # spawn the workers
    for i in range(WORKER_COUNT):
        p = ctx.Process(target=worker, args=(i, q_in, q_out))
        p.start()
        workers.append(p)
        active_workers += 1

    # Create and use an output file context manager
    with open(OUTPUT_FN, "wt") as outf:
        successes = 0
        fails = 0
        # process as long as there are active workers
        while active_workers > 0:
            # get the next GeoSJON object from a worker
            (code, coords, lines, p_off, n_off) = q_out.get()
            if code == POISON_PILL_MSG:
                # Poison pill:  decrement the worker count
                logging.info("Worker shutdown detected")
                active_workers -= 1
            elif code != FAILED_DECODING_MSG:
                # We have a valid geosjon object: write it to the output file
                outf.write(f"{code}\t{coords}\t{lines}\t{p_off}\t{n_off}\n")
                successes += 1
            else:
                # decoding failure: update counter
                fails += 1
            responses_received += 1
            if responses_received % 1000 == 0:
                # periodically update the status message and flush output
                print_progress(successes, fails, start_time)

        print_progress(successes, fails, start_time)
        print("\nDone")

    # allow worker processes to terminate
    for w in workers:
        w.join()

    # clean up
    loader.join()
    q_in.close()
    q_out.close()
