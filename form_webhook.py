import json

# Maps field label (lowercase) to DB column names.
# Works for both Typeform and Tally.so webhooks.
FIELD_MAP = {
    # Email
    "email":                                            "email",
    "what's your email address?":                       "email",
    "what is your email address?":                      "email",
    # Full name
    "full_name":                                        "full_name",
    "full name":                                        "full_name",
    "what's your full name?":                           "full_name",
    "what is your full name?":                          "full_name",
    # Current job title
    "current_job_title":                                "current_job_title",
    "current job title":                                "current_job_title",
    "what is your current job title?":                  "current_job_title",
    # Location
    "location":                                         "location",
    "where are you based?":                             "location",
    "where are you based? (city, country)":             "location",
    # Career goal
    "career_goal":                                      "career_goal",
    "career goal":                                      "career_goal",
    "what is your career goal?":                        "career_goal",
    # Salary expectation
    "salary_expectation":                               "salary_expectation",
    "salary expectation":                               "salary_expectation",
    "annual gross salary":                              "salary_expectation",
    "what is your annual gross salary expectation?":    "salary_expectation",
    "what are your annual gross salary expectations?":  "salary_expectation",
}


def parse_tally_lead(payload: dict) -> dict:
    """
    Extract lead fields from a Tally.so webhook payload.
    Tally structure:
    {
      "eventType": "FORM_RESPONSE",
      "data": {
        "responseId": "...",
        "fields": [
          {"key": "...", "label": "What's your email?", "type": "INPUT_EMAIL", "value": "..."},
          ...
        ]
      }
    }
    """
    lead = {
        "tiktok_lead_id":       None,
        "tiktok_form_id":       None,
        "tiktok_ad_id":         None,
        "tiktok_campaign_id":   None,
        "raw_payload":          json.dumps(payload),
        "email":                None,
        "full_name":            None,
        "current_job_title":    None,
        "location":             None,
        "career_goal":          None,
        "salary_expectation":   None,
    }

    data = payload.get("data", {})
    response_id = data.get("responseId")
    if response_id:
        lead["tiktok_lead_id"] = f"tally_{response_id}"

    lead["tiktok_form_id"] = data.get("formId") or payload.get("formId")

    for field in data.get("fields", []):
        label = (field.get("label") or "").lower().strip()
        db_col = FIELD_MAP.get(label)
        if not db_col:
            continue
        value = field.get("value")
        if isinstance(value, list):
            # Multiple choice — join labels
            value = ", ".join(str(v) for v in value)
        if value is not None:
            lead[db_col] = str(value)

    return lead


def parse_typeform_lead(payload: dict) -> dict:
    """
    Extract lead fields from a Typeform webhook payload.
    Returns a flat dict ready for DB insertion.

    Typeform payload structure:
    {
      "form_response": {
        "token": "...",
        "answers": [
          {"field": {"ref": "email", "type": "email"}, "type": "email", "email": "..."},
          {"field": {"ref": "full_name", "type": "short_text"}, "type": "text", "text": "..."},
          ...
        ]
      }
    }
    """
    lead = {
        "tiktok_lead_id":       None,
        "tiktok_form_id":       None,
        "tiktok_ad_id":         None,
        "tiktok_campaign_id":   None,
        "raw_payload":          json.dumps(payload),
        "email":                None,
        "full_name":            None,
        "current_job_title":    None,
        "location":             None,
        "career_goal":          None,
        "salary_expectation":   None,
    }

    form_response = payload.get("form_response", {})

    # Use Typeform response token as a unique ID to prevent duplicates
    token = form_response.get("token")
    if token:
        lead["tiktok_lead_id"] = f"typeform_{token}"

    # Store form ID
    lead["tiktok_form_id"] = payload.get("form_id") or form_response.get("form_id")

    for answer in form_response.get("answers", []):
        field = answer.get("field", {})

        # Try field ref first, fall back to field title
        key = (field.get("ref") or field.get("title") or "").lower().strip()
        db_col = FIELD_MAP.get(key)

        if not db_col:
            continue

        # Extract value based on answer type
        answer_type = answer.get("type", "")
        if answer_type == "email":
            value = answer.get("email", "")
        elif answer_type == "text":
            value = answer.get("text", "")
        elif answer_type == "choice":
            value = answer.get("choice", {}).get("label", "")
        elif answer_type == "choices":
            value = ", ".join(
                c.get("label", "") for c in answer.get("choices", {}).get("labels", [])
            )
        else:
            # Fallback: grab whichever value key exists
            for vkey in ("text", "email", "number", "boolean", "date", "url", "phone_number"):
                if vkey in answer:
                    value = str(answer[vkey])
                    break
            else:
                value = ""

        if value:
            lead[db_col] = value

    return lead
