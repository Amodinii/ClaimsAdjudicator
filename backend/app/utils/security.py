import copy
from typing import Any, Dict

# Fields to redact in logs
SENSITIVE_FIELDS = {"member_id", "name", "patient_name", "phone", "email", "aadhaar"}

def redact_phi(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scrubs sensitive keys from a dictionary for safe logging.
    Does not modify the original dictionary.
    """
    if not isinstance(data, dict):
        return data

    safe_data = copy.deepcopy(data)
    
    def _scrub(d):
        for key, value in d.items():
            if key in SENSITIVE_FIELDS:
                d[key] = "***REDACTED***"
            elif isinstance(value, dict):
                _scrub(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        _scrub(item)
    
    _scrub(safe_data)
    return safe_data