
import os
from pathlib import Path
from typing import Any, Dict
import json

ROOT = Path(__file__).resolve().parents[3]  
DATA_DIR = os.environ.get("PLUM_DATA_DIR", ROOT/"backend" /"data") 
POLICY_FILE = os.environ.get("PLUM_POLICY_FILE", str(Path(DATA_DIR) / "policy_terms.json"))
TEST_CASES_FILE = os.environ.get("PLUM_TEST_CASES_FILE", str(Path(DATA_DIR) / "test_cases.json"))

LOG_DIR = Path(os.environ.get("PLUM_LOG_DIR", str(ROOT / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
