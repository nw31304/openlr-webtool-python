from shapely import LineString

import geoutils.geoutils
from openlr_dereferencer_python.openlr_dereferencer.decoding import MapObjects
from openlr_dereferencer_python.openlr_dereferencer.decoding.line_decoding import LineLocation
from tomtom_sqlite import TomTomMapReaderSQLite
from .analysis_result import AnalysisResult
import typer
from geoutils.geoutils import buffer_wgs84_ls, split_line

def build_decoded_ls(decode_result: LineLocation) -> LineString:
    tmp = geoutils.geoutils.join_lines([line.geometry for line in decode_result.lines])
    if decode_result.p_off > 0:
        _, front = split_line(tmp, decode_result.p_off)
    else:
        front = tmp
    if decode_result.n_off > 0:
        back, _ = split_line(front, decode_result.n_off)
    else:
        back = front
    return back

def analyze(olr: str, ls: LineString, map_reader: TomTomMapReaderSQLite, buffer: int = 20) -> AnalysisResult:
    """Analyze a location reference against a map"""

    # build a buffer around the source linestring
    buffered_ls = buffer_wgs84_ls(ls, buffer)
    # decode the string against the target map
    decode_result: MapObjects = map_reader.match(olr)

    match decode_result:
        case None:
            return AnalysisResult.UNKNOWN_ERROR
        case LineLocation():
            pass
        case _:
            return AnalysisResult.UNSUPPORTED_LOCATION_TYPE
    decoded_ls = build_decoded_ls(decode_result)
    if buffered_ls.contains(decoded_ls):
        return AnalysisResult.OK


    return AnalysisResult.OK