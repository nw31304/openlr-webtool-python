from enum import Enum


class AnalysisResult(Enum):
    OK = 0,
    MISSING_PATH = 1,
    ALTERNATE_SHORTEST_PATH = 2,
    FRC_MISMATCH = 3,
    FOW_MISMATCH = 4,
    BEARING_MISMATCH = 5,
    PATH_TOO_LONG = 7,
    PATH_TOO_SHORT = 8,
    UNSUPPORTED_LOCATION_TYPE = 8,
    UNKNOWN_ERROR = 9
