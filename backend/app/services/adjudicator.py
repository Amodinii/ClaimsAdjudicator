import re
import time
from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta, timezone
from ..utils.logging_utils import setup_logging
from ..utils.exception_handlers import ServiceError
from ..utils.security import redact_phi

logger = setup_logging()

POLICY = {
  "policy_id": "PLUM_OPD_2024",
  "policy_name": "Plum OPD Advantage",
  "effective_date": "2024-01-01",
  "policy_holder": {
    "company": "TechCorp Solutions Pvt Ltd",
    "employees_covered": 500,
    "dependents_covered": True
  },
  "coverage_details": {
    "annual_limit": 50000,
    "per_claim_limit": 5000,
    "family_floater_limit": 150000,
    "consultation_fees": {
      "covered": True,
      "sub_limit": 2000,
      "copay_percentage": 10,
      "network_discount": 20
    },
    "diagnostic_tests": {
      "covered": True,
      "sub_limit": 10000,
      "pre_authorization_required": False,
      "covered_tests": [
        "Blood tests", "Urine tests", "X-rays", "ECG",
        "Ultrasound", "MRI (with pre-auth)", "CT Scan (with pre-auth)"
      ]
    },
    "pharmacy": {
      "covered": True,
      "sub_limit": 15000,
      "generic_drugs_mandatory": True,
      "branded_drugs_copay": 30
    },
    "dental": {
      "covered": True,
      "sub_limit": 10000,
      "routine_checkup_limit": 2000,
      "procedures_covered": ["Filling", "Extraction", "Root canal", "Cleaning"],
      "cosmetic_procedures": False
    },
    "vision": {
      "covered": True,
      "sub_limit": 5000,
      "eye_test_covered": True,
      "glasses_contact_lenses": True,
      "lasik_surgery": False
    },
    "alternative_medicine": {
      "covered": True,
      "sub_limit": 8000,
      "covered_treatments": ["Ayurveda", "Homeopathy", "Unani"],
      "therapy_sessions_limit": 20
    }
  },
  "waiting_periods": {
    "initial_waiting": 30,
    "pre_existing_diseases": 365,
    "maternity": 270,
    "specific_ailments": {
      "diabetes": 90,
      "hypertension": 90,
      "joint_replacement": 730
    }
  },
  "exclusions": [
    "Cosmetic procedures", "Weight loss treatments", "Infertility treatments",
    "Experimental treatments", "Self-inflicted injuries", "Adventure sports injuries",
    "War and nuclear risks", "HIV/AIDS treatment", "Alcoholism/drug abuse treatment",
    "Non-allopathic treatments (except listed)",
    "Vitamins and supplements (unless prescribed for deficiency)"
  ],
  "claim_requirements": {
    "documents_required": [
      "Original bills and receipts", "Prescription from registered doctor",
      "Diagnostic test reports (if applicable)", "Pharmacy bills with prescription",
      "Doctor's registration number must be visible", "Patient details must match policy records"
    ],
    "submission_timeline_days": 30,
    "minimum_claim_amount": 500
  },
  "network_hospitals": [
    "Apollo Hospitals", "Fortis Healthcare", "Max Healthcare",
    "Manipal Hospitals", "Narayana Health"
  ],
  "cashless_facilities": {
    "available": True,
    "network_only": True,
    "pre_approval_required": False,
    "instant_approval_limit": 5000
  }
}

# --- CONFIGURATION ---
ADJUDICATION_CONFIG = {
    "weights": {
        "extraction_quality": 0.4,
        "policy_alignment": 0.3,
        "document_integrity": 0.3
    },
    "doctor_reg_regex": r"^[A-Z]{2,10}[-\/\s]?([A-Z]{2,3}[-\/\s]?)?\d{1,6}[-\/\s]?\d{4}$"
}

# --- HELPER FUNCTIONS ---

def parse_date(d):
    if not d: return None
    if isinstance(d, (int, float)):
        try: return datetime.fromtimestamp(d, tz=timezone.utc)
        except: return None
    d = str(d).strip()
    try: return datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
    except: pass
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try: return datetime.strptime(d, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return None

def money(x):
    try: return round(float(x or 0.0), 2)
    except: return 0.0

def validate_doctor_reg(reg_no: str) -> bool:
    if not reg_no: return False
    clean_reg = reg_no.strip().upper()
    pattern = ADJUDICATION_CONFIG["doctor_reg_regex"]
    return bool(re.match(pattern, clean_reg))

# --- CHECK FUNCTIONS ---

def check_eligibility(claim: Dict[str, Any]) -> Tuple[bool, List[str], Dict]:
    flags = []
    notes = {}
    try:
        eff = POLICY.get("effective_date")
        td = parse_date(claim.get("treatment_date"))
        if eff:
            eff_d = parse_date(eff)
            if td and eff_d and td < eff_d:
                flags.append("POLICY_INACTIVE")
                notes["policy_active_from"] = eff_d.strftime("%Y-%m-%d")
        
        member = claim.get("member") or {}
        join_date = parse_date(member.get("join_date"))
        if not join_date: join_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        if join_date and td:
            waiting = POLICY.get("waiting_periods", {}).get("specific_ailments", {})
            diag = (claim.get("diagnosis") or "").lower()
            for cond, days in waiting.items():
                if cond.lower() in diag:
                    eligible_on = join_date + timedelta(days=int(days))
                    if td < eligible_on:
                        flags.append("WAITING_PERIOD")
                        notes["waiting_period_until"] = eligible_on.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Eligibility check failed: {e}")
        flags.append("ELIGIBILITY_CHECK_ERROR")
    return (len(flags) == 0, flags, notes)

def check_documents(claim: Dict[str, Any]) -> Tuple[bool, List[str]]:
    flags = []
    try:
        docs = claim.get("documents", [])
        doc_types = [d.get("type", "").lower() for d in docs]
        items = claim.get("items", [])
        
        if not docs and not items: 
             flags.append("MISSING_DOCUMENTS")
             
        has_medicines = any("pharmacy" in i.get("category","").lower() or "medicine" in i.get("category","").lower() for i in items)
        has_prescription = any("prescription" in dt for dt in doc_types)
        
        if has_medicines and not has_prescription:
            if not claim.get("diagnosis"):
                flags.append("MISSING_DOCUMENTS")

        doc_reg = claim.get("doctor_reg")
        if not doc_reg:
            for d in docs:
                if d.get("doctor_reg"):
                    doc_reg = d.get("doctor_reg")
                    break
        
        if doc_reg:
            if not validate_doctor_reg(doc_reg):
                flags.append("DOCTOR_REG_INVALID")

    except Exception as e:
        logger.error(f"Document check failed: {e}")
        
    return (len(flags) == 0, list(set(flags)))

def check_coverage_and_limits(claim: Dict[str, Any]) -> Tuple[bool, List[str], float, List[Dict]]:
    flags = []
    breakdown = [] 
    
    try:
        total_claim = money(claim.get("total_amount", 0.0))
        breakdown.append({"label": "Total Claimed Amount", "amount": total_claim, "type": "info"})
        
        approved_running_total = 0.0
        
        # --- 1. Item Level Validation ---
        policy_exclusions = POLICY.get("exclusions", [])
        extended_exclusions = policy_exclusions + ["Whitening", "Aesthetic", "Beautification", "Cosmetic"]
        
        items = claim.get("items", [])
        if not items and total_claim > 0:
            items = [{"name": "Medical Charges", "amount": total_claim, "category": "General"}]

        specific_limit_applied = False
        has_consultation = False
        is_alternative = False

        for item in items:
            name = (item.get("name") or "").lower()
            category = (item.get("category") or "").lower()
            amt = money(item.get("amount", 0.0))
            
            if "alternative" in category or "ayurveda" in category or "homeopathy" in category:
                is_alternative = True

            is_excluded = False
            for ex in extended_exclusions:
                if ex.lower() in name or ex.lower() in category:
                    is_excluded = True
                    break
            
            if is_excluded:
                flags.append("SERVICE_NOT_COVERED")
                breakdown.append({"label": f"Excluded: {item.get('name')}", "amount": -amt, "type": "deduction"})
            else:
                approved_running_total += amt
                if "consultation" in category or "consultation" in name:
                    has_consultation = True

        # --- 2. Sub-limits ---
        diagnosis = (claim.get("diagnosis") or "").lower()
        
        if "root canal" in diagnosis or "tooth" in diagnosis or "dental" in diagnosis:
            dental_limit = money(POLICY["coverage_details"]["dental"]["sub_limit"])
            specific_limit_applied = True
            if approved_running_total > dental_limit:
                diff = approved_running_total - dental_limit
                flags.append("SUB_LIMIT_EXCEEDED")
                breakdown.append({"label": "Dental Sub-limit Exceeded", "amount": -diff, "type": "deduction"})
                approved_running_total = dental_limit

        # --- 3. Global Per Claim Limit ---
        if not specific_limit_applied:
            per_claim_limit = money(POLICY["coverage_details"]["per_claim_limit"])
            if approved_running_total > per_claim_limit:
                diff = approved_running_total - per_claim_limit
                flags.append("PER_CLAIM_EXCEEDED")
                breakdown.append({"label": "Per-Claim Limit Exceeded", "amount": -diff, "type": "deduction"})
                approved_running_total = per_claim_limit

        # --- 4. Network Discount ---
        hospital = claim.get("hospital") or {}
        in_network = False
        if hospital.get("name"):
            for net_hosp in POLICY.get("network_hospitals", []):
                if net_hosp.lower() in hospital["name"].lower():
                    in_network = True
                    break
        
        network_discount_applied = False
        if in_network:
            disc_pct = money(POLICY["coverage_details"]["consultation_fees"]["network_discount"])
            discount = (approved_running_total * disc_pct) / 100
            if discount > 0:
                breakdown.append({"label": f"Network Discount ({disc_pct}%)", "amount": -discount, "type": "deduction"})
                approved_running_total -= discount
                network_discount_applied = True

        # --- 5. Co-pay ---
        should_apply_copay = has_consultation and not network_discount_applied and not specific_limit_applied and not is_alternative
        
        if should_apply_copay:
            copay_pct = money(POLICY["coverage_details"]["consultation_fees"]["copay_percentage"])
            copay = (approved_running_total * copay_pct) / 100
            if copay > 0:
                breakdown.append({"label": f"Co-pay ({copay_pct}%)", "amount": -copay, "type": "deduction"})
                approved_running_total -= copay

        # Final
        approved_running_total = max(0.0, approved_running_total)
        breakdown.append({"label": "Final Approved Amount", "amount": approved_running_total, "type": "final"})

    except Exception as e:
        logger.error(f"Coverage check failed: {e}")
        raise ServiceError("Coverage & limits validation error")
    
    return (len(flags) == 0, flags, round(approved_running_total, 2), breakdown)

def fraud_checks(claim: Dict[str, Any]) -> Tuple[bool, List[str]]:
    flags = []
    if money(claim.get("total_amount")) > 50000:
        flags.append("HIGH_VALUE_CLAIM_MANUAL_REVIEW")
    if int(claim.get("prev_claims_same_day", 0)) > 1:
        flags.append("MULTIPLE_CLAIMS_SAME_DAY")
    return (len(flags) == 0, flags)

def compute_granular_confidence(claim: Dict[str, Any], rule_flags: List[str]) -> Tuple[float, Dict]:
    breakdown = {
        "extraction_conf": float(claim.get("_extraction_conf", 0.85)),
        "doc_conf": 1.0,
        "policy_conf": 1.0
    }
    if "MISSING_DOCUMENTS" in rule_flags: breakdown["policy_conf"] = 0.0
    elif "REJECTED" in rule_flags: breakdown["policy_conf"] = 0.95 
    
    score = (breakdown["extraction_conf"] * 0.4) + (breakdown["policy_conf"] * 0.6)
    return round(min(1.0, score), 2), breakdown

def adjudicate_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.perf_counter()
    safe_log = redact_phi(claim)
    logger.info(f"Adjudicating claim: Amount={safe_log.get('total_amount')}")

    result = {"decision": None, "approved_amount": 0.0, "reasons": [], "confidence": 0.0}
    
    try:
        elig_ok, elig_flags, elig_notes = check_eligibility(claim)
        doc_ok, doc_flags = check_documents(claim)
        fraud_ok, fraud_flags = fraud_checks(claim)
        cov_ok, cov_flags, approved_amount, breakdown = check_coverage_and_limits(claim)
        
        reasons = list(set(elig_flags + doc_flags + cov_flags + fraud_flags))
        result["notes"] = elig_notes
        
        total_claimed = money(claim.get("total_amount"))
        
        if not elig_ok:
            result["decision"] = "REJECTED"
            approved_amount = 0.0
        elif not doc_ok:
            result["decision"] = "REJECTED"
            approved_amount = 0.0
        elif not fraud_ok:
            result["decision"] = "MANUAL_REVIEW"
            approved_amount = 0.0
        elif "PER_CLAIM_EXCEEDED" in reasons:
            result["decision"] = "REJECTED"
            approved_amount = 0.0
        elif "SERVICE_NOT_COVERED" in reasons and approved_amount == 0:
             result["decision"] = "REJECTED"
        else:
            deductions = [b for b in breakdown if b['type'] == 'deduction']
            simple_deductions = all(any(x in d['label'] for x in ["Co-pay", "Discount"]) for d in deductions)
            
            if approved_amount == total_claimed:
                result["decision"] = "APPROVED"
            elif approved_amount > 0 and simple_deductions:
                result["decision"] = "APPROVED"
            elif approved_amount > 0:
                result["decision"] = "PARTIAL"
            else:
                result["decision"] = "REJECTED"

        if result["decision"] in ["REJECTED", "MANUAL_REVIEW"]:
            result["approved_amount"] = 0.0
            for item in breakdown:
                if item["type"] == "final":
                    item["amount"] = 0.0
        else:
            result["approved_amount"] = approved_amount

        confidence, conf_breakdown = compute_granular_confidence(claim, reasons)
        
        result.update({
            "confidence": confidence,
            "confidence_breakdown": conf_breakdown,
            "reasons": reasons,
            "breakdown": breakdown,
            "processing_time_ms": round((time.perf_counter() - start_time) * 1000, 2)
        })
        
        logger.info(f"Adjudication complete. Decision={result['decision']}")

    except Exception as e:
        logger.error(f"Adjudication error: {e}")
        raise ServiceError("Adjudication logic failed")
        
    return result