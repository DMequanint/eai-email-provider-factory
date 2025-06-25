# email_app/fake_api.py
# Author: Dessalegn Mequanint Yehuala
# Description: Simulates external email API responses for testing purposes.

import uuid

# --- Simulate SendGrid API ---
def fake_sendgrid_api(payload: dict) -> dict:
    """
    Simulates a SendGrid API call.
    Checks for basic payload structure and specific error triggers.
    """
    print(f"--- Fake SendGrid API Call ---")
    print(f"Payload: {payload}")

    # Basic checks simulating API validation
    if not payload.get('personalizations') or not payload['personalizations'][0].get('to'):
        return {"errors": [{"message": "Missing recipient"}]}
    if not payload.get('from') or not payload['from'].get('email'):
        return {"errors": [{"message": "Missing sender"}]}
    if not payload.get('subject'):
        return {"errors": [{"message": "Missing subject"}]}
    if not payload.get('content') or not payload['content'][0].get('value'):
        return {"errors": [{"message": "Missing content"}]}

    # Simulate specific error triggers
    to_email = payload['personalizations'][0]['to'][0]['email']
    if to_email == "error@example.com":
        return {"errors": [{"message": "Simulated SendGrid API error: invalid recipient"}]}
    if payload.get('subject') == "error_trigger_sendgrid":
        return {"errors": [{"message": "Simulated SendGrid API error: internal server error"}]}

    # Simulate success response
    return {
        "messages": [
            {"id": str(uuid.uuid4()), "status": "queued"}
        ]
    }

# --- Simulate Mailgun API ---
def fake_mailgun_api(payload: dict) -> dict:
    """
    Simulates a Mailgun API call.
    Checks for basic payload structure and specific error triggers.
    """
    print(f"--- Fake Mailgun API Call ---")
    print(f"Payload: {payload}")

    # Basic checks simulating API validation
    if not payload.get('to'):
        return {"message": "Recipient not specified", "status": "failed"}
    if not payload.get('from'):
        return {"message": "Sender not specified", "status": "failed"}
    if not payload.get('subject'):
        return {"message": "Subject not specified", "status": "failed"}
    if not payload.get('text') and not payload.get('html'):
        return {"message": "Message content not specified", "status": "failed"}

    # Simulate specific error triggers
    to_email = payload['to'] # Mailgun uses single 'to' field string for simple cases
    if to_email == "error@mailgun.com":
        return {"message": "Simulated Mailgun API error: invalid address", "status": "failed"}
    if payload.get('subject') == "error_trigger_mailgun":
        return {"message": "Simulated Mailgun API error: internal issue", "status": "failed"}

    # Simulate success response
    return {
        "id": f"<{uuid.uuid4()}@mailgun.org>",
        "message": "Queued. Thank you."
    }


