from typing import List, Optional
from app.engine.models import NormalizedEvidence

ERROR_STATUS_CODES = [500, 502, 503, 504]
KNOWN_ERROR_CODES = ["DATABASE_TIMEOUT", "CONNECTION_TIMEOUT", "NULL_OBJECT_ACCESS"]

def classify_signal(ev: NormalizedEvidence) -> None:
    if ev.status_code in ERROR_STATUS_CODES:
        ev.is_error = True
    elif ev.error_code in KNOWN_ERROR_CODES:
        ev.is_error = True
    elif ev.event_type.lower() in ["error", "exception"]:
        ev.is_error = True
    elif ev.error_message:
        ev.is_error = True
    else:
        ev.is_error = False
