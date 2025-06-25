# email_app/new/base.py
# Defines the abstract base class for all email providers.

from abc import ABC, abstractmethod
from functools import wraps
import re # For basic email format validation
from email_app import errors, settings # Import custom errors and settings


class BaseEmailProvider(ABC):
    """
    Abstract base class for all email providers.
    Defines the common interface and orchestration for sending emails.
    """
    def __init__(self):
        self._to_email = None
        self._subject = None
        self._text_content = None
        self._html_content = None
        self._sender_email = settings.DEFAULT_SENDER_EMAIL # Default sender from settings

    # --- Chainable Setter Methods (Task 2) ---
    def set_to_email(self, email: str):
        """Sets the recipient email address. Chainable."""
        self._to_email = email
        return self

    def set_subject(self, subject: str):
        """Sets the email subject. Chainable."""
        self._subject = subject
        return self

    def set_text_content(self, content: str):
        """Sets the plain text content of the email. Chainable."""
        self._text_content = content
        # Ensure only one content type is set, or prioritize
        self._html_content = None # Clear HTML if text content is set
        return self

    def set_html_content(self, content: str):
        """Sets the HTML content of the email. Chainable."""
        self._html_content = content
        # Ensure only one content type is set, or prioritize
        self._text_content = None # Clear text if HTML content is set
        return self

    def set_sender_email(self, email: str):
        """Sets the sender email address, overriding default. Chainable."""
        self._sender_email = email
        return self

    # --- Core Abstract Methods (to be implemented by concrete providers) ---

    @abstractmethod
    def _validate_input(self):
        """
        Abstract method to validate all input parameters (recipient, subject, content).
        Concrete providers must implement this with their specific rules.
        Raises appropriate exceptions from email_app.errors.
        """
        # Common checks can go here, but specific formats are for concrete providers.
        if not self._to_email:
            raise errors.MissingRequiredFieldError("Recipient email is required.")
        if not self._subject:
            raise errors.MissingRequiredFieldError("Subject is required.")
        if not self._text_content and not self._html_content:
            raise errors.MissingRequiredFieldError("Email content (text or HTML) is required.")

        # Basic email format validation (allowing unicode, common for modern Python)
        # This regex broadly covers many valid formats including unicode characters in local part
        # For full IDN validation (xn-- domains), an external library like 'idna' would be needed,
        # but adhering to 'dependency-free', we keep it simple.
        email_regex = re.compile(r'[^@]+@[^@]+\.[^@]+') # Simplified, just checks @ and dot
        if not email_regex.fullmatch(self._to_email):
             raise errors.InvalidEmailAddressError(f"Recipient email '{self._to_email}' is not valid.")
        if not email_regex.fullmatch(self._sender_email):
             raise errors.InvalidEmailAddressError(f"Sender email '{self._sender_email}' is not valid.")


    @abstractmethod
    def _prepare_payload(self) -> dict:
        """
        Abstract method to prepare the API-specific payload (Task 3 & 4).
        Concrete providers must implement this to transform common email data
        into their API's required JSON/form data structure.
        """
        pass

    @abstractmethod
    def _send_request(self, payload: dict) -> dict:
        """
        Abstract method to send the prepared payload to the external API (Task 3 & 4).
        Concrete providers will call their specific fake_api function here.
        """
        pass

    @abstractmethod
    def _parse_response(self, response: dict) -> dict:
        """
        Abstract method to parse the external API's response into a standardized format.
        Concrete providers must implement this to return a common success/error dict.
        Raises email_app.errors.ProviderApiError on API-level errors.
        """
        pass

    # --- Orchestration Method ---
    def send(self) -> dict:
        """
        Orchestrates the entire email sending process:
        1. Validates all input parameters.
        2. Prepares the API-specific payload.
        3. Sends the request to the external API.
        4. Parses the API response into a standard format.
        """
        self._validate_input() # Calls provider-specific validation
        payload = self._prepare_payload()
        api_response = self._send_request(payload)
        return self._parse_response(api_response)


