# Proctoring event penalties

EVENT_PENALTIES = {
    "face_not_detected": 0.10,
    "multiple_faces_detected": 0.30,
    "gaze_off_screen": 0.05,
    "tab_switched": 0.15,
    "fullscreen_exited": 0.10,
    "paste_attempted": 0.20
}


# Risk level thresholds

LOW_RISK_THRESHOLD = 0.80

MEDIUM_RISK_THRESHOLD = 0.50

# Final assessment weights
PROJECT_SCORE_WEIGHT = 0.40
VIVA_SCORE_WEIGHT = 0.40
INTEGRITY_SCORE_WEIGHT = 0.20


# --------------------------------------------------
# UPLOAD SECURITY CONFIGURATION
# --------------------------------------------------
MAX_ZIP_SIZE_MB = 10
MAX_ZIP_SIZE_BYTES = (
    MAX_ZIP_SIZE_MB * 1024 * 1024
)