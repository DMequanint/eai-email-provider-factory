# email_app/new/factory.py
# Implements the Factory Design Pattern for email providers.

from email_app.new.base import BaseEmailProvider
from email_app.new.sendgrid_provider import SendGridEmailProvider
from email_app.new.mailgun_provider import MailgunEmailProvider
from email_app import errors


def email_provider_factory(provider_name: str) -> BaseEmailProvider:
    """
    Factory function to return the correct email provider instance
    (e.g., SendGridEmailProvider, MailgunEmailProvider)
    based on the given provider_name.

    Args:
        provider_name (str): The name of the email provider (e.g., 'sendgrid', 'mailgun').

    Returns:
        BaseEmailProvider: An instance of the requested email provider.

    Raises:
        ProviderNotImplementedError: If the provided provider_name is not recognized.
    """
    if provider_name.lower() == 'sendgrid':
        return SendGridEmailProvider()
    elif provider_name.lower() == 'mailgun':
        return MailgunEmailProvider()
    else:
        raise errors.ProviderNotImplementedError(
            f"Email provider '{provider_name}' is not implemented."
        )


