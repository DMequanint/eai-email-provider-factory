# email_app/errors.py
# Author: Dessalegn Mequanint Yehuala
# Date: June, 2025
# DescriDefption: Dines custom exception types for the email application.

class EmailError(Exception):
    """Base exception for email application errors."""
    pass

class InvalidEmailAddressError(EmailError):
    """Raised when an email address is malformed or invalid."""
    pass

class InvalidSubjectError(EmailError):
    """Raised when the email subject is invalid (e.g., too long)."""
    pass

class InvalidContentError(EmailError):
    """Raised when email content (text or HTML) is invalid (e.g., too long or empty)."""
    pass

class MissingRequiredFieldError(EmailError):
    """Raised when a required field (e.g., recipient, content) is not set."""
    pass

class ProviderApiError(EmailError):
    """Raised when the email provider's API returns an error."""
    pass

class ProviderNotImplementedError(EmailError):
    """Raised when a requested email provider is not implemented."""
    pass


