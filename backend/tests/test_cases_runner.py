import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to python path to allow imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.services.adjudicator import adjudicate_claim
from backend.app.core.config import TEST_CASES_FILE
from backend.app.utils.logging_utils import setup_logging

logger = setup_logging()

def load_tests(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_test_input(tc_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    ADAPTER: Converts 'test_cases.json' input format 
    into the internal schema expected by the Adjudicator.
    """
    normalized = {
        "total_amount": float(tc_input.get("claim_amount", 0.0)),
        "treatment_date": tc_input.get("treatment_date"),
        "diagnosis": None,
        "member": {
            "member_id": tc_input.get("member_id"),
            "join_date": tc_input.get("member_join_date")
        },
        "items": [],
        "documents": [],
        "hospital": {
            "name": tc_input.get("hospital"),
            "in_network": False # Default, override below
        },
        "prev_claims_same_day": tc_input.get("previous_claims_same_day", 0),
        "structured": True, # Tell system this is perfect data
        "_extraction_conf": 1.0
    }

    # Handle Hospital Network Logic for Test Cases
    # (In real app this is done via Policy lookup, but we map input here)
    hosp_name = tc_input.get("hospital", "")
    if hosp_name and any(x in hosp_name for x in ["Apollo", "Fortis", "Max"]):
        normalized["hospital"]["in_network"] = True

    raw_docs = tc_input.get("documents", {})
    
    # 1. Extract Prescription Data
    if "prescription" in raw_docs:
        presc = raw_docs["prescription"]
        normalized["diagnosis"] = presc.get("diagnosis")
        normalized["doctor_reg"] = presc.get("doctor_reg") # Lift to top level
        
        normalized["documents"].append({
            "type": "prescription",
            "doctor_reg": presc.get("doctor_reg")
        })
        
        # Add medicines/procedures to items with 0 cost (cost usually comes from bill)
        # This helps the logic know that medicines were prescribed
        if "medicines_prescribed" in presc:
            for med in presc["medicines_prescribed"]:
                normalized["items"].append({"name": med, "amount": 0, "category": "Pharmacy"})
        
        if "procedures" in presc:
            for proc in presc["procedures"]:
                normalized["items"].append({"name": proc, "amount": 0, "category": "Procedure"})

    # 2. Extract Bill Data
    if "bill" in raw_docs:
        bill = raw_docs["bill"]
        normalized["documents"].append({"type": "bill"})
        
        for key, val in bill.items():
            # Skip metadata keys if they exist
            if key in ["bill_no", "date"]: continue

            category = "General"
            name_lower = key.lower()
            
            # Categorize based on key name
            if "consultation" in name_lower: category = "Consultation"
            elif "medicine" in name_lower or "pharmacy" in name_lower: category = "Pharmacy"
            elif "test" in name_lower or "scan" in name_lower or "mri" in name_lower: category = "Diagnostic"
            elif "root_canal" in name_lower or "tooth" in name_lower: category = "Dental"
            elif "whitening" in name_lower: category = "Dental - Cosmetic"
            elif "therapy" in name_lower: category = "Alternative"
            elif "diet" in name_lower: category = "Wellness"
            
            # If value is numeric, add as item
            if isinstance(val, (int, float)):
                normalized["items"].append({
                    "name": key.replace("_", " ").title(),
                    "amount": float(val),
                    "category": category
                })
    
    # Edge Case: TC004 (Missing Docs) - Input has bill but we need to ensure adapter doesn't fake a prescription
    # The loop above handles this correctly (only adds prescription doc if key exists)

    return normalized

def run_all():
    path = Path(TEST_CASES_FILE)
    print(f"\n Loading test cases from: {path}")
    
    try:
        data = load_tests(path)
        cases = data.get("test_cases", data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"Error loading test cases: {e}")
        return False

    passed = 0
    failed = 0
    
    # Table Header
    print(f"{'ID':<8} | {'EXPECTED':<15} | {'ACTUAL':<15} | {'AMT DIFF':<10} | {'RESULT'}")
    print("-" * 80)

    for tc in cases:
        tcid = tc.get("case_id", "UNKNOWN")
        raw_input = tc.get("input_data", {})
        expected = tc.get("expected_output", {})
        
        # 1. Adapt Input
        adj_input = normalize_test_input(raw_input)
        
        # 2. Run Logic
        out = adjudicate_claim(adj_input)
        
        # 3. Assertions
        decision_match = out.get("decision") == expected.get("decision")
        
        amount_match = True
        exp_amount = expected.get("approved_amount")
        act_amount = out.get("approved_amount", 0.0)
        
        # Only check amount if expected amount is provided
        if exp_amount is not None:
            if abs(act_amount - exp_amount) > 1.0: # Allow 1.0 tolerance
                amount_match = False

        # 4. Formatting Output
        status = "PASS" if (decision_match and amount_match) else "FAIL"
        diff = f"{act_amount - exp_amount:+.0f}" if exp_amount is not None else "N/A"
        
        print(f"{tcid:<8} | {expected.get('decision'):<15} | {out.get('decision'):<15} | {diff:<10} | {status}")
        
        if not (decision_match and amount_match):
            failed += 1
            # Detailed debug info for failures
            print(f"   >> Reasons: {out.get('reasons')}")
            print(f"   >> Breakdown: {[ (b['label'], b['amount']) for b in out.get('breakdown', []) ]}")
        else:
            passed += 1

    print("-" * 80)
    print(f"Results: {passed} Passed, {failed} Failed. Total: {len(cases)}\n")
    return failed == 0

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)