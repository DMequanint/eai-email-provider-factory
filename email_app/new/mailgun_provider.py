# email_app/new/mailgun_provider.py
# Author: Dessalegn Mequanint Yehuala
# Description: Concrete implementation for Mailgun Email Provider, now capable of real API calls.

from email_app.new.base import BaseEmailProvider
from email_app.fake_api import fake_mailgun_api # Still imported for potential unit tests if needed
from email_app import errors, settings
import requests # Import the requests library for HTTP calls
import os # <--- ADDED THIS IMPORT: Necessary for os.getenv


class MailgunEmailProvider(BaseEmailProvider):
    """
    Implements the BaseEmailProvider for Mailgun API.
    Can send real emails via Mailgun's API.
    """
    def _validate_input(self):
        """
        Validates all input parameters specific to Mailgun.
        Extends base validation with Mailgun specific content type checks and lengths.
        """
        super()._validate_input() # Call common validations from base class

        if not self._text_content and not self._html_content:
            raise errors.MissingRequiredFieldError("Either plain text or HTML content is required.")

        if self._text_content and len(self._text_content) > settings.MAX_TEXT_CONTENT_LENGTH:
            raise errors.InvalidContentError(f"Plain text content too long for Mailgun (max {settings.MAX_TEXT_CONTENT_LENGTH} chars).")
        if self._html_content and len(self._html_content) > settings.MAX_HTML_CONTENT_LENGTH:
            raise errors.InvalidContentError(f"HTML content too long for Mailgun (max {settings.MAX_HTML_CONTENT_LENGTH} chars).")
        if len(self._subject) > settings.MAX_SUBJECT_LENGTH:
            raise errors.InvalidSubjectError(f"Subject too long for Mailgun (max {settings.MAX_SUBJECT_LENGTH} chars).")
        if len(self._to_email) > settings.MAX_EMAIL_ADDRESS_LENGTH:
            raise errors.InvalidEmailAddressError(f"Recipient email too long (max {settings.MAX_EMAIL_ADDRESS_LENGTH} chars).")
        if len(self._sender_email) > settings.MAX_EMAIL_ADDRESS_LENGTH:
            raise errors.InvalidEmailAddressError(f"Sender email too long (max {settings.MAX_EMAIL_ADDRESS_LENGTH} chars).")


    def _prepare_payload(self) -> dict:
        """
        Prepares the API-specific payload for Mailgun.
        Mailgun typically uses 'from', 'to', 'subject', 'text', 'html' as form fields.
        """
        payload = {
            "from": self._sender_email, # Mailgun uses a simple 'from' string
            "to": self._to_email,       # Mailgun uses a simple 'to' string
            "subject": self._subject,
            # API key is handled in _send_request via Basic Auth.
            # Domain is handled in _send_request via URL path.
        }
        if self._text_content:
            payload["text"] = self._text_content
        if self._html_content:
            payload["html"] = self._html_content
        return payload

    def _send_request(self, payload: dict) -> dict:
        """
        Sends the prepared payload to the actual Mailgun API via HTTP POST (form-encoded).
        Falls back to fake_mailgun_api if a real API key isn't configured.
        """
        use_fake_api = os.getenv("USE_FAKE_API_MAILGUN", "False").lower() == "true"

        if use_fake_api or not settings.MAILGUN_API_KEY or "DEFAULT_WARNING" in settings.MAILGUN_API_KEY:
            print("--- Using fake_mailgun_api (no real API key or USE_FAKE_API_MAILGUN=True) ---")
            # If using fake, ensure the payload matches what fake expects for auth_key checks
            payload_for_fake = payload.copy()
            # Pass the key to fake API for its check, removing default warning string if present
            payload_for_fake['auth_key'] = settings.MAILGUN_API_KEY.replace("_DEFAULT_WARNING", "")
            return fake_mailgun_api(payload_for_fake)
        else:
            print("--- Sending via REAL Mailgun API ---")
            # Mailgun uses HTTP Basic Auth with 'api' as username and API key as password
            auth = ("api", settings.MAILGUN_API_KEY)
            
            # The Mailgun endpoint requires the domain in the URL path:
            mailgun_url = f"{settings.MAILGUN_API_BASE_URL}{settings.MAILGUN_DOMAIN}/messages"

            try:
                # Mailgun expects form-encoded data, not JSON for simple messages
                response = requests.post(mailgun_url, auth=auth, data=payload)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json() # Return JSON response
            except requests.exceptions.RequestException as e:
                raise errors.ProviderApiError(f"Mailgun API Request failed: {e}") from e

    def _parse_response(self, response: dict) -> dict:
        """
        Parses the response from the Mailgun API into a standardized format.
        Handles both successful (2xx) and explicit error responses.
        """
        if response.get("message") == "Queued. Thank you." and "id" in response:
            return {"status": "sent", "provider": "mailgun", "message_id": response["id"]}
        elif response.get("message") and response.get("status") == "failed":
            error_message = response.get("message", "Unknown Mailgun API error.")
            raise errors.ProviderApiError(f"Mailgun API Error: {error_message}")
        else:
            raise errors.ProviderApiError(f"Unknown or unexpected Mailgun API response: {response}")


