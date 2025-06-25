# email_app/new/sendgrid_provider.py
# Concrete implementation for SendGrid Email Provider, now capable of real API calls.

from email_app.new.base import BaseEmailProvider
from email_app.fake_api import fake_sendgrid_api # Still imported for potential unit tests if needed
from email_app import errors, settings
import requests # Import the requests library for HTTP calls
import os # <--- ADDED THIS IMPORT: Necessary for os.getenv


class SendGridEmailProvider(BaseEmailProvider):
    """
    Implements the BaseEmailProvider for SendGrid API.
    Can send real emails via SendGrid's API.
    """
    def _validate_input(self):
        """
        Validates all input parameters specific to SendGrid.
        Extends base validation with SendGrid specific content type checks and lengths.
        """
        super()._validate_input() # Call common validations from base class

        if self._text_content and self._html_content:
            raise errors.InvalidContentError("Cannot set both plain text and HTML content for SendGrid.")
        if not self._text_content and not self._html_content:
            raise errors.MissingRequiredFieldError("Either plain text or HTML content is required.")

        if self._text_content and len(self._text_content) > settings.MAX_TEXT_CONTENT_LENGTH:
            raise errors.InvalidContentError(f"Plain text content too long for SendGrid (max {settings.MAX_TEXT_CONTENT_LENGTH} chars).")
        if self._html_content and len(self._html_content) > settings.MAX_HTML_CONTENT_LENGTH:
            raise errors.InvalidContentError(f"HTML content too long for SendGrid (max {settings.MAX_HTML_CONTENT_LENGTH} chars).")
        if len(self._subject) > settings.MAX_SUBJECT_LENGTH:
            raise errors.InvalidSubjectError(f"Subject too long for SendGrid (max {settings.MAX_SUBJECT_LENGTH} chars).")
        if len(self._to_email) > settings.MAX_EMAIL_ADDRESS_LENGTH:
            raise errors.InvalidEmailAddressError(f"Recipient email too long (max {settings.MAX_EMAIL_ADDRESS_LENGTH} chars).")
        if len(self._sender_email) > settings.MAX_EMAIL_ADDRESS_LENGTH:
            raise errors.InvalidEmailAddressError(f"Sender email too long (max {settings.MAX_EMAIL_ADDRESS_LENGTH} chars).")

    def _prepare_payload(self) -> dict:
        """
        Prepares the API-specific JSON payload for SendGrid.
        """
        content_type = "text/plain" if self._text_content else "text/html"
        content_value = self._text_content if self._text_content else self._html_content

        return {
            "personalizations": [
                {"to": [{"email": self._to_email}]}
            ],
            "from": {"email": self._sender_email},
            "subject": self._subject,
            "content": [
                {
                    "type": content_type,
                    "value": content_value
                }
            ],
            # API key is typically sent in the Authorization header, not in the JSON body for SendGrid.
            # It will be handled in _send_request.
        }

    def _send_request(self, payload: dict) -> dict:
        """
        Sends the prepared payload to the actual SendGrid API via HTTP POST.
        Falls back to fake_sendgrid_api if a real API key isn't configured,
        or if explicitly set for testing (e.g., via an environment variable 'USE_FAKE_API').
        """
        # Determine whether to use the real API or the fake one
        # This allows easy switching for testing vs. production/integration testing
        use_fake_api = os.getenv("USE_FAKE_API_SENDGRID", "False").lower() == "true"

        if use_fake_api or not settings.SENDGRID_API_KEY or "DEFAULT_WARNING" in settings.SENDGRID_API_KEY:
            print("--- Using fake_sendgrid_api (no real API key or USE_FAKE_API_SENDGRID=True) ---")
            # If using fake, ensure the payload matches what fake expects for api_key checks
            payload_for_fake = payload.copy()
            # Pass the key to fake API for its check, removing default warning string if present
            payload_for_fake['api_key'] = settings.SENDGRID_API_KEY.replace("_DEFAULT_WARNING", "")
            return fake_sendgrid_api(payload_for_fake)
        else:
            print("--- Sending via REAL SendGrid API ---")
            headers = {
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            }
            try:
                # requests.post sends a POST request with the JSON payload
                response = requests.post(settings.SENDGRID_API_URL, json=payload, headers=headers)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json() # Return JSON response
            except requests.exceptions.RequestException as e:
                # Catch network errors, timeouts, HTTP errors etc.
                raise errors.ProviderApiError(f"SendGrid API Request failed: {e}") from e

    def _parse_response(self, response: dict) -> dict:
        """
        Parses the response from the SendGrid API into a standardized format.
        Handles both successful (2xx) and explicit error responses.
        """
        if "messages" in response and response["messages"] and response["messages"][0].get("status") == "queued":
            return {"status": "sent", "provider": "sendgrid", "message_id": response["messages"][0].get("id", "N/A")}
        elif "errors" in response and response["errors"]:
            # SendGrid error responses usually have an 'errors' array
            error_message = response["errors"][0].get("message", "Unknown SendGrid API error.")
            raise errors.ProviderApiError(f"SendGrid API Error: {error_message}")
        else:
            # For a real API, you'd typically check response.status_code first.
            # This covers cases not explicitly covered by mock's success/error keys,
            # or unexpected non-200 responses that didn't raise_for_status for some reason.
            raise errors.ProviderApiError(f"Unknown or unexpected SendGrid API response: {response}")


