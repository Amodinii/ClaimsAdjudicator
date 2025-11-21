import json
from pathlib import Path
from ..app.services.adjudicator import adjudicate_claim
from ..app.core.config import TEST_CASES_FILE
from ..app.utils.logging_utils import setup_logging

logger = setup_logging()

def load_tests(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_all():
    path = TEST_CASES_FILE
    logger.info("Loading test cases from %s", path)
    tests = load_tests(path)
    cases = tests.get("cases", tests if isinstance(tests, list) else [])
    all_ok = True
    for tc in cases:
        tcid = tc.get("id")
        inp = tc.get("input", {})
        expected = tc.get("expected", {})
        out = adjudicate_claim(inp)
        ok = True
        # compare decision if present
        if expected.get("decision") and out.get("decision") != expected.get("decision"):
            ok = False
        # compare approved_amount if present (tolerance)
        if expected.get("approved_amount") is not None:
            if abs(out.get("approved_amount", 0.0) - expected.get("approved_amount", 0.0)) > 0.01:
                ok = False
        print(f"[{tcid}] OK={ok} decision={out.get('decision')} approved={out.get('approved_amount')} conf={out.get('confidence')}")
        if not ok:
            all_ok = False
    return all_ok

if __name__ == "__main__":
    ok = run_all()
    print("ALL PASSED?:", ok)
