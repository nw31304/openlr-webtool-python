from openlr_dereferencer.decoding import Config
from openlr import FRC
from typing import Dict

#: When comparing an LRP FOW with a candidate's FOW, this matrix defines
#: how well the candidate's FOW fits as replacement for the expected value.
#: The usage is `fow_standin_score[lrp's fow][candidate's fow]`.
#: It returns the score.
STRICT_FOW_STAND_IN_SCORE = [
    [0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.5],  # 0 = Undefined FOW
    [0.50, 1.00, 0.75, 0.00, 0.00, 0.00, 0.00, 0.0],  # 1 = Motorway
    [0.50, 0.75, 1.00, 0.75, 0.50, 0.00, 0.00, 0.0],  # 2 = Multiple carriage way
    [0.50, 0.00, 0.75, 1.00, 0.50, 0.50, 0.00, 0.0],  # 3 = Single carriage way
    [0.50, 0.00, 0.50, 0.50, 1.00, 0.50, 0.00, 0.0],  # 4 = Roundabout
    [0.50, 0.00, 0.00, 0.50, 0.50, 1.00, 0.00, 0.0],  # 5 = Traffic square
    [0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.0],  # 6 = Sliproad
    [0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.0],  # 7 = Other FOW
]

# Decoding is first attempted using strict decoding parameters,
# and then retried with more lenient ones if the first decoding
# failed. This is the strict version of the LFRC -> FRC disctionary.
#
# This maps the LFRC in the LRP to the minimal FRC that will be
# accepted

STRICT_TOLERATED_LFRC: Dict[FRC, FRC] = { FRC.FRC0: FRC.FRC1,
                                          FRC.FRC1: FRC.FRC2,
                                          FRC.FRC2: FRC.FRC3,
                                          FRC.FRC3: FRC.FRC4,
                                          FRC.FRC4: FRC.FRC5,
                                          FRC.FRC5: FRC.FRC6,
                                          FRC.FRC6: FRC.FRC7,
                                          FRC.FRC7: FRC.FRC7,
                                          }

# The relaxed version of the LFRC -> FRC dictionary
RELAXED_TOLERATED_LFRC: Dict[FRC, FRC] = {
    FRC.FRC0: FRC.FRC1,
    FRC.FRC1: FRC.FRC3,
    FRC.FRC2: FRC.FRC3,
    FRC.FRC3: FRC.FRC5,
    FRC.FRC4: FRC.FRC5,
    FRC.FRC5: FRC.FRC7,
    FRC.FRC6: FRC.FRC7,
    FRC.FRC7: FRC.FRC7,
}

# A strict configuration
StrictConfig = Config(
    tolerated_lfrc=STRICT_TOLERATED_LFRC,
    max_bear_deviation=30,
    search_radius=30,
    geo_weight=0.66,
    frc_weight=0.17,
    fow_weight=0.17,
    bear_weight=0.0,
    fow_standin_score=STRICT_FOW_STAND_IN_SCORE
)

# A relaxed configuration
RelaxedConfig = Config(
    tolerated_lfrc=RELAXED_TOLERATED_LFRC,
    search_radius=50,
    geo_weight=0.66,
    frc_weight=0.17,
    fow_weight=0.17,
    bear_weight=0.0,
    fow_standin_score=STRICT_FOW_STAND_IN_SCORE
)
