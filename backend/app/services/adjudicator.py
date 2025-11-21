from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
from ..core.config import POLICY_FILE, load_json
from ..utils.logging_utils import setup_logging
from ..utils.exception_handlers import ServiceError

logger = setup_logging()
POLICY = load_json(POLICY_FILE) or {}

def parse_date(d):
    if not d:
        return None
    if isinstance(d, (int, float)):
        try:
            return datetime.fromtimestamp(d)
        except Exception:
            return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(d, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(d)
    except Exception:
        return None

def money(x):
    try:
        return float(x or 0.0)
    except Exception:
        return 0.0

def check_eligibility(claim: Dict[str, Any]) -> Tuple[bool, List[str], Dict]:
    flags = []
    notes = {}
    try:
        eff = POLICY.get("effective_from")
        td = parse_date(claim.get("treatment_date"))
        if eff:
            eff_d = parse_date(eff)
            if td and eff_d and td < eff_d:
                flags.append("POLICY_INACTIVE")
                notes["policy_active_from"] = eff_d.strftime("%Y-%m-%d")
        member = claim.get("member") or {}
        join_date = parse_date(member.get("join_date"))
        if join_date and td:
            waiting = POLICY.get("waiting_periods", {})
            diag = (claim.get("diagnosis") or "").lower()
            for cond, days in waiting.items():
                if cond.lower() in diag:
                    eligible_on = join_date + timedelta(days=int(days))
                    if td < eligible_on:
                        flags.append("WAITING_PERIOD")
                        notes["waiting_period_until"] = eligible_on.strftime("%Y-%m-%d")
    except Exception as e:
        logger.exception("Eligibility check failed: %s", e)
        raise ServiceError("Eligibility validation error")
    return (len(flags) == 0, flags, notes)

def check_documents(claim: Dict[str, Any]) -> Tuple[bool, List[str]]:
    flags = []
    try:
        docs = claim.get("documents", [])
        types = { (d.get("type") or "").lower() for d in docs }
        if not ("prescription" in types or "bill" in types or claim.get("structured", False)):
            flags.append("MISSING_DOCUMENTS")
        for d in docs:
            reg = d.get("doctor_reg")
            if reg and len(reg.strip()) < 5:
                flags.append("DOCTOR_REG_INVALID")
    except Exception as e:
        logger.exception("Document check failed: %s", e)
        raise ServiceError("Document validation error")
    return (len(flags) == 0, list(set(flags)))

def check_coverage_and_limits(claim: Dict[str, Any]) -> Tuple[bool, List[str], float, Dict]:
    flags = []
    try:
        total_claim = money(claim.get("total_amount", 0.0))
        approved_amount = 0.0
        details = {}
        per_claim_limit = money(POLICY.get("per_claim_limit", 1e12))
        if total_claim > per_claim_limit:
            flags.append("PER_CLAIM_EXCEEDED")
        excluded = POLICY.get("excluded_services", [])
        covered_items = []
        uncovered_items = []
        for item in claim.get("items", []):
            name = (item.get("name") or "").lower()
            amt = money(item.get("amount", 0.0))
            excluded_found = any(ex.lower() in name for ex in excluded)
            if excluded_found:
                uncovered_items.append({"name": name, "amount": amt, "reason": "SERVICE_NOT_COVERED"})
            else:
                covered_items.append({"name": name, "amount": amt})
        sublimits = POLICY.get("sublimits", {})
        for c in covered_items:
            nm = c["name"]
            amt = c["amount"]
            lim = sublimits.get(nm)
            approved_amount += min(amt, money(lim)) if lim is not None else amt
        # network discount then copay
        network_discount = 0.0
        hospital = claim.get("hospital") or {}
        if hospital.get("in_network"):
            nd = money(POLICY.get("network_discount_pct", 0.0))
            network_discount = (nd / 100.0) * approved_amount
            approved_amount -= network_discount
        copay_pct = money(POLICY.get("copay_pct", 0.0))
        copay_amount = (copay_pct / 100.0) * approved_amount
        approved_amount -= copay_amount
        details.update({
            "sum_claim": total_claim,
            "sum_covered_items": sum(i["amount"] for i in covered_items),
            "uncovered_items": uncovered_items,
            "network_discount": round(network_discount, 2),
            "copay_amount": round(copay_amount, 2)
        })
    except Exception as e:
        logger.exception("Coverage check failed: %s", e)
        raise ServiceError("Coverage & limits validation error")
    return (len(flags) == 0, flags, round(max(0.0, approved_amount), 2), details)

def fraud_checks(claim: Dict[str, Any]) -> Tuple[bool, List[str]]:
    flags = []
    try:
        prev_same_day = int(claim.get("prev_claims_same_day") or 0)
        amt = money(claim.get("total_amount", 0.0))
        threshold = money(POLICY.get("fraud_manual_review_threshold", 10000))
        prev_threshold = int(POLICY.get("prev_same_day_threshold", 2))
        if prev_same_day >= prev_threshold and amt > threshold:
            flags.append("FRAUD_SUSPECT_MANUAL_REVIEW")
    except Exception as e:
        logger.exception("Fraud check failed: %s", e)
        raise ServiceError("Fraud detection error")
    return (len(flags) == 0, flags)

def compute_confidence(claim: Dict[str, Any], extraction_conf: float, doc_ok: bool, policy_ok: bool, fraud_ok: bool) -> Tuple[float, Dict]:
    breakdown = {
        "extraction_conf": float(extraction_conf or 0.0),
        "doc_conf": 1.0 if doc_ok else 0.0,
        "policy_conf": 1.0 if policy_ok else 0.0,
        "fraud_conf": 1.0 if fraud_ok else 0.0,
    }
    # weights - adjustable via policy later
    w_ex, w_doc, w_pol, w_f = 0.5, 0.2, 0.2, 0.1
    overall = min(1.0, (breakdown["extraction_conf"]*w_ex +
                        breakdown["doc_conf"]*w_doc +
                        breakdown["policy_conf"]*w_pol +
                        breakdown["fraud_conf"]*w_f))
    return round(overall, 3), breakdown

def adjudicate_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Adjudicating claim for treatment_date=%s total_amount=%s", claim.get("treatment_date"), claim.get("total_amount"))
    result = {"decision": None, "approved_amount": 0.0, "reasons": [], "confidence": 0.0, "notes": {}}
    try:
        extraction_conf = float(claim.get("_extraction_conf", 0.9))
        elig_ok, elig_flags, elig_notes = check_eligibility(claim)
        doc_ok, doc_flags = check_documents(claim)
        cov_ok, cov_flags, approved_amount, cov_details = check_coverage_and_limits(claim)
        fraud_ok, fraud_flags = fraud_checks(claim)
        reasons = list(set(elig_flags + doc_flags + cov_flags + fraud_flags))
        result["notes"].update(elig_notes)
        result["notes"].update(cov_details)
        # decision logic (deterministic priority)
        if "POLICY_INACTIVE" in reasons or "WAITING_PERIOD" in reasons:
            result["decision"] = "REJECTED"
            result["approved_amount"] = 0.0
        elif "MISSING_DOCUMENTS" in reasons or "DOCTOR_REG_INVALID" in reasons:
            result["decision"] = "REJECTED"
            result["approved_amount"] = 0.0
        elif "PER_CLAIM_EXCEEDED" in reasons:
            result["decision"] = "REJECTED"
            result["approved_amount"] = 0.0
        elif any(r.startswith("FRAUD") for r in reasons):
            result["decision"] = "MANUAL_REVIEW"
            result["approved_amount"] = 0.0
        else:
            uncovered = result["notes"].get("uncovered_items", [])
            if uncovered and approved_amount > 0:
                result["decision"] = "PARTIAL_APPROVAL"
            else:
                result["decision"] = "APPROVED"
            result["approved_amount"] = approved_amount
        confidence, breakdown = compute_confidence(claim, extraction_conf, doc_ok, cov_ok, fraud_ok)
        result["confidence"] = confidence
        result["confidence_breakdown"] = breakdown
        result["reasons"] = reasons
        logger.info("Decision: %s, approved_amount=%s, confidence=%s", result["decision"], result["approved_amount"], result["confidence"])
    except ServiceError:
        raise
    except Exception as e:
        logger.exception("Unhandled error during adjudication: %s", e)
        raise ServiceError("Adjudication failed")
    return result
