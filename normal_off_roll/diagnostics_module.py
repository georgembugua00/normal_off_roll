
import re

# ---------------- OCR-Based Diagnostic Matching ------------------

# Common phrases mapped to diagnostic tags
error_patterns = {
    "the service is currently unavailable": "SERVICE_DOWN",
    "unable to buy airtime": "AIRTIME_FAIL",
    "agent number is incorrect": "AGENT_INPUT_ERROR",
    "transaction failed, amobilenumbern value is not unique": "UNBARRING_ISSUE",
    "customer number is invalid": "CUSTOMER_INPUT_ERROR",
    "not authorized to sell this device": "5G_DEVICE_AUTH",
    "superline message": "SUPERLINE_AGENT_INPUT_ERROR",
    "supervision period exceeded": "INACTIVE_AGENT",
    "no airtel money message": "BUNDLE_NO_AM_MESSAGE",
    "account is locked": "ACCOUNT_LOCKED",
    "did not receive commission": "MISSING_COMMISSION",
    "already registered with given msisdn": "DUPLICATE_ROUTER"
}

# Diagnostic explanations and recommendations
diagnostic_map = {
    "SERVICE_DOWN": {
        "explanation": "Airtel Money system might be temporarily down.",
        "diagnostic": "Advise agent to retry later. Escalate if persistent."
    },
    "AIRTIME_FAIL": {
        "explanation": "Agent failed to buy airtime, possibly due to float or system error.",
        "diagnostic": "Verify agent float. If issue persists, escalate to backend."
    },
    "AGENT_INPUT_ERROR": {
        "explanation": "Agent or customer number was incorrectly entered.",
        "diagnostic": "Verify MSISDN and retry. Escalate if correct but still fails."
    },
    "UNBARRING_ISSUE": {
        "explanation": "Agent MSISDN is barred due to duplicate mobile number.",
        "diagnostic": "Submit escalation for unbarring via system admin."
    },
    "CUSTOMER_INPUT_ERROR": {
        "explanation": "Invalid customer number entry during deposit or transfer.",
        "diagnostic": "Reconfirm number format. Use correct MSISDN."
    },
    "5G_DEVICE_AUTH": {
        "explanation": "This line is not authorized to register a 5G router.",
        "diagnostic": "Clear cache and retry. If issue persists, escalate."
    },
    "SUPERLINE_AGENT_INPUT_ERROR": {
        "explanation": "Incorrect superline or agent number during float transfer.",
        "diagnostic": "Validate both MSISDNs and reattempt."
    },
    "INACTIVE_AGENT": {
        "explanation": "Agent has exceeded inactivity threshold.",
        "diagnostic": "Verify inactivity reason. Backend to reset if valid."
    },
    "BUNDLE_NO_AM_MESSAGE": {
        "explanation": "Bundle purchased, but no AM confirmation or data allocation.",
        "diagnostic": "Confirm deduction. Re-push or escalate for refund."
    },
    "ACCOUNT_LOCKED": {
        "explanation": "Agent account is locked for transactions.",
        "diagnostic": "Unlock request must be initiated. Contact 444 if urgent."
    },
    "MISSING_COMMISSION": {
        "explanation": "Agent completed transaction but no commission disbursed.",
        "diagnostic": "Check transaction logs and escalate for manual disbursement."
    },
    "DUPLICATE_ROUTER": {
        "explanation": "MSISDN already registered for 5G router.",
        "diagnostic": "Validate registration status. Avoid duplicate provisioning."
    }
}

# Match known issue patterns in text
def match_error_tag(text):
    text = text.lower()
    for phrase, tag in error_patterns.items():
        if phrase in text:
            return tag
    return "UNKNOWN"

# Retrieve explanation and fix recommendation
def diagnostics_lookup(tag):
    return diagnostic_map.get(tag, {
        "explanation": "No known match for the error.",
        "diagnostic": "Manually escalate with agent MSISDN and screenshot."
    })

# Run full diagnostic
def run_diagnostic_from_message_or_image_text(text):
    tag = match_error_tag(text)
    explanation, fix = diagnostics_lookup(tag).values()
    return {
        "diagnostic_tag": tag,
        "explanation": explanation,
        "resolution_hint": fix
    }
