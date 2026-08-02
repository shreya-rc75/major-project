# Configurable constants for the clinical stage estimator.
# Move thresholds and weights here so they can be tuned centrally.

# Weights for combining model probabilities
WEIGHT_CANCER = 1.0
WEIGHT_HIGH_GRADE = 0.6
WEIGHT_LOW_GRADE = 0.25

# Clinical weights
WEIGHT_HPV_POSITIVE = 0.25
WEIGHT_BIOPSY_INVASIVE = 1.0
WEIGHT_BIOPSY_HIGH_GRADE = 0.5
WEIGHT_BIOPSY_LOW_GRADE = 0.15
WEIGHT_IMAGING_SPREAD = 0.8
WEIGHT_IMAGING_MASS = 0.3
WEIGHT_SYMPTOMS = 0.15

# Cell-derived feature weights and thresholds
NUCLEUS_AREA_THRESHOLD = 300.0
WEIGHT_NUCLEUS_AREA = 0.3
SOLIDITY_THRESHOLD = 0.5
WEIGHT_SOLIDITY = 0.2

# General
MAX_SCORE = 3.0

# Stage mapping thresholds on normalized score
STAGE_THRESHOLDS = {
    "Stage 0": (0.0, 0.15),
    "Stage I": (0.15, 0.35),
    "Stage II": (0.35, 0.6),
    "Stage III": (0.6, 0.85),
    "Stage IV": (0.85, 1.0),
}
