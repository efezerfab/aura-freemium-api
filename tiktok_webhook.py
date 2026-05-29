import hashlib
import hmac
import os
import json

TIKTOK_WEBHOOK_SECRET = os.environ.get("TIKTOK_WEBHOOK_SECRET", "")

# Maps TikTok form field labels (lowercase) to our DB column names
FIELD_MAP = {
    "email":                              "email",
    "full name":                          "full_name",
    "name":                               "full_name",
    "current role":                       "current_job_title",
    "current role/title":                 "current_job_title",
    "job title":                          "current_job_title",
    "title":                              "current_job_title",
    "location":                           "location",
    "city":                               "location",
    "city/country":                       "location",
    "career goal":                        "career_goal",
    "career goals":                       "career_goal",
    "annual gross salary expectations":   "salary_expectation",
    "salary expectation":                 "salary_expectation",
    "salary":                             "salary_expectation",
    "expected salary":                    "salary_expectation",
}


def verify_tiktok_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """Return True if X-TikTok-Signature matches HMAC-SHA256 of payload."""
    if not TIKTOK_WEBHOOK_SECRET:
        return True  # Skip verification in local dev if secret not set
    expected = hmac.new(
        TIKTOK_WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def parse_tiktok_lead(payload: dict) -> dict:
    """
    Extract lead fields from TikTok webhook payload.
    Returns a flat dict ready for DB insertion.
    """
    lead = {
        "tiktok_lead_id":    payload.get("lead_id"),
        "tiktok_form_id":    payload.get("form_id"),
        "tiktok_ad_id":      payload.get("ad_id"),
        "tiktok_campaign_id": payload.get("campaign_id"),
        "raw_payload":       json.dumps(payload),
        "email":             None,
        "full_name":         None,
        "current_job_title":      None,
        "location":          None,
        "career_goal":       None,
        "salary_expectation": None,
    }

    # TikTok sends answers as a list: [{"name": "field_label", "value": "answer"}]
    for field in payload.get("field_data", []):
        key = field.get("name", "").lower().strip()
        value = field.get("value", "")
        db_col = FIELD_MAP.get(key)
        if db_col:
            lead[db_col] = value

    return lead
