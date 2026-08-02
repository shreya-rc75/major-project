# Constants for risk prediction heuristics

# Model contribution weights
WEIGHT_CANCER = 0.6
WEIGHT_HIGH_GRADE = 0.3
WEIGHT_LOW_GRADE = 0.1

# Clinical weights
WEIGHT_HPV = 0.15
WEIGHT_BIOPSY_INVASIVE = 0.4
WEIGHT_BIOPSY_HIGH_GRADE = 0.2
WEIGHT_BIOPSY_LOW_GRADE = 0.05
WEIGHT_IMAGING_SPREAD = 0.3

# Cell features
NUCLEUS_AREA_THRESHOLD = 300.0
WEIGHT_NUCLEUS_AREA = 0.15
WEIGHT_SOLIDITY = 0.1
SOLIDITY_THRESHOLD = 0.5

# Scaling and normalization
MAX_BASE = 2.0  # upper bound for raw base before normalization
SCALE_1Y = 0.25
SCALE_3Y = 0.6
SCALE_5Y = 0.95

# Risk category thresholds
RISK_THRESHOLDS = {
    "low": 0.10,
    "medium": 0.30,
    "high": 1.0,
}
