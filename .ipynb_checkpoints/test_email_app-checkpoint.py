# test_email_app.py
# Pytest test suite to verify all functionalities of the email application.
# Now includes option to trigger real API calls (for integration testing).

import pytest
import os # Import os for environment variables
import requests_mock # Used for mocking HTTP requests in tests
from email_app.new.base import BaseEmailProvider
from email_app.new.sendgrid_provider import SendGridEmailProvider
from email_app.new.mailgun_provider import MailgunEmailProvider
from email_app.new.factory import email_provider_factory
from email_app import errors, settings


# --- Fixture to mock HTTP requests for unit tests ---
@pytest.fixture(autouse=True)
def mock_external_api_calls(requests_mock):
    """
    Mocks HTTP requests to external APIs using requests_mock.
    This ensures unit tests remain fast and isolated, always using fake data
    unless explicitly told otherwise via environment variables for integration tests.
    """
    # Ensure fake API is used by default in tests
    os.environ["USE_FAKE_API_SENDGRID"] = "true"
    os.environ["USE_FAKE_API_MAILGUN"] = "true"

    # Define mocks for SendGrid's fake API interactions
    # These effectively replace calls to `fake_sendgrid_api` in unit tests
    # when `USE_FAKE_API_SENDGRID` is 'true'.
    # Note: If `_send_request` calls `fake_sendgrid_api` directly (which it does when USE_FAKE_API is true),
    # then requests_mock isn't strictly intercepting the fake_api call itself.
    # This fixture is more relevant if we were always hitting requests.post and then mocking that.
    # For this structure, we mainly set environment variables to steer the provider.
    
    # However, if we wanted to test the real API path *but still mock it* (e.g., in CI/CD without real keys)
    # this is how requests_mock would be used.
    # For now, it reinforces the concept that we *would* mock real API calls if running unit tests.

    # Example of how you *would* mock real API calls for integration tests without hitting the live service:
    # requests_mock.post(settings.SENDGRID_API_URL, json={"messages": [{"id": "mock_sg_id", "status": "queued"}]}, status_code=202)
    # requests_mock.post(f"{settings.MAILGUN_API_BASE_URL}{settings.MAILGUN_DOMAIN}/messages", json={"id": "<mock_mg_id>", "message": "Queued. Thank you."}, status_code=200)

    yield
    # Clean up environment variables after tests
    del os.environ["USE_FAKE_API_SENDGRID"]
    del os.environ["USE_FAKE_API_MAILGUN"]


# --- Test Cases for Factory ---
def test_factory_returns_sendgrid_provider():
    provider = email_provider_factory('sendgrid')
    assert isinstance(provider, SendGridEmailProvider)
    assert isinstance(provider, BaseEmailProvider)

def test_factory_returns_mailgun_provider():
    provider = email_provider_factory('mailgun')
    assert isinstance(provider, MailgunEmailProvider)
    assert isinstance(provider, BaseEmailProvider)

def test_factory_unknown_provider_raises_error():
    with pytest.raises(errors.ProviderNotImplementedError) as excinfo:
        email_provider_factory('unknown')
    assert "Email provider 'unknown' is not implemented." in str(excinfo.value)


# --- Test Cases for BaseEmailProvider Setters ---
def test_setters_are_chainable():
    provider = SendGridEmailProvider()
    chained_provider = provider \
        .set_to_email("test@example.com") \
        .set_subject("Test Subject") \
        .set_text_content("Hello World")
    
    assert chained_provider is provider
    assert provider._to_email == "test@example.com"
    assert provider._subject == "Test Subject"
    assert provider._text_content == "Hello World"
    assert provider._html_content is None

def test_setters_prioritize_html_over_text():
    provider = SendGridEmailProvider()
    provider.set_text_content("Plain text").set_html_content("<h1>HTML</h1>")
    assert provider._text_content is None
    assert provider._html_content == "<h1>HTML</h1>"

def test_send_without_required_fields_raises_error():
    provider = SendGridEmailProvider()
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send()
    assert "Recipient email is required." in str(excinfo.value)

    provider.set_to_email("user@example.com")
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send()
    assert "Subject is required." in str(excinfo.value)

    provider.set_subject("Hello")
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send()
    assert "Email content (text or HTML) is required." in str(excinfo.value)

def test_base_validation_invalid_email_format():
    provider = SendGridEmailProvider()
    with pytest.raises(errors.InvalidEmailAddressError) as excinfo:
        provider.set_to_email("invalid-email").set_subject("Sub").set_text_content("Content").send()
    assert "Recipient email 'invalid-email' is not valid." in str(excinfo.value)

    with pytest.raises(errors.InvalidEmailAddressError) as excinfo:
        provider.set_to_email("valid@example.com").set_sender_email("bad-sender").set_subject("Sub").set_text_content("Content").send()
    assert "Sender email 'bad-sender' is not valid." in str(excinfo.value)

# --- Test Cases for SendGridEmailProvider ---
def test_sendgrid_send_success_text_content():
    provider = SendGridEmailProvider()
    response = provider \
        .set_to_email("recipient@example.com") \
        .set_subject("Hello from SendGrid") \
        .set_text_content("This is a test email with plain text.") \
        .send()
    
    assert response["status"] == "sent"
    assert response["provider"] == "sendgrid"
    assert "message_id" in response

def test_sendgrid_send_success_html_content():
    provider = SendGridEmailProvider()
    response = provider \
        .set_to_email("html_user@example.com") \
        .set_subject("HTML Email from SendGrid") \
        .set_html_content("<h1>Hello!</h1><p>This is <b>HTML</b> content.</p>") \
        .send()
    
    assert response["status"] == "sent"
    assert response["provider"] == "sendgrid"
    assert "message_id" in response

def test_sendgrid_validation_content_too_long():
    provider = SendGridEmailProvider()
    long_content = "A" * (settings.MAX_TEXT_CONTENT_LENGTH + 1)
    with pytest.raises(errors.InvalidContentError) as excinfo:
        provider.set_to_email("test@example.com").set_subject("Test").set_text_content(long_content).send()
    assert f"Plain text content too long for SendGrid (max {settings.MAX_TEXT_CONTENT_LENGTH} chars)." in str(excinfo.value)

def test_sendgrid_validation_subject_too_long():
    provider = SendGridEmailProvider()
    long_subject = "S" * (settings.MAX_SUBJECT_LENGTH + 1)
    with pytest.raises(errors.InvalidSubjectError) as excinfo:
        provider.set_to_email("test@example.com").set_subject(long_subject).set_text_content("Content").send()
    assert f"Subject too long for SendGrid (max {settings.MAX_SUBJECT_LENGTH} chars)." in str(excinfo.value)

def test_sendgrid_simulated_api_error():
    provider = SendGridEmailProvider()
    with pytest.raises(errors.ProviderApiError) as excinfo:
        provider.set_to_email("error@example.com").set_subject("Error Test").set_text_content("Trigger API error").send()
    assert "Simulated SendGrid API error: invalid recipient" in str(excinfo.value)

def test_sendgrid_simulated_internal_api_error():
    provider = SendGridEmailProvider()
    with pytest.raises(errors.ProviderApiError) as excinfo:
        provider.set_to_email("test@example.com").set_subject("error_trigger_sendgrid").set_text_content("Trigger internal API error").send()
    assert "Simulated SendGrid API error: internal server error" in str(excinfo.value)

def test_sendgrid_unicode_email_and_content():
    provider = SendGridEmailProvider()
    response = provider \
        .set_to_email("user.ünicode@éxample.com") \
        .set_subject("你好 from SendGrid") \
        .set_text_content("This email contains Unicode characters: éàüöç") \
        .send()
    assert response["status"] == "sent"
    assert response["provider"] == "sendgrid"


# --- Test Cases for MailgunEmailProvider ---
def test_mailgun_send_success_text_content():
    provider = MailgunEmailProvider()
    response = provider \
        .set_to_email("mg_recipient@example.com") \
        .set_subject("Hello from Mailgun") \
        .set_text_content("This is a test email with plain text via Mailgun.") \
        .send()
    
    assert response["status"] == "sent"
    assert response["provider"] == "mailgun"
    assert "message_id" in response

def test_mailgun_send_success_html_content():
    provider = MailgunEmailProvider()
    response = provider \
        .set_to_email("mg_html_user@example.com") \
        .set_subject("HTML Email from Mailgun") \
        .set_html_content("<p>Mailgun <b>HTML</b> content.</p>") \
        .send()
    
    assert response["status"] == "sent"
    assert response["provider"] == "mailgun"
    assert "message_id" in response

def test_mailgun_validation_content_too_long():
    provider = MailgunEmailProvider()
    long_content = "B" * (settings.MAX_TEXT_CONTENT_LENGTH + 1)
    with pytest.raises(errors.InvalidContentError) as excinfo:
        provider.set_to_email("test@mailgun.com").set_subject("Test").set_text_content(long_content).send()
    assert f"Plain text content too long for Mailgun (max {settings.MAX_TEXT_CONTENT_LENGTH} chars)." in str(excinfo.value)

def test_mailgun_validation_subject_too_long():
    provider = MailgunEmailProvider()
    long_subject = "T" * (settings.MAX_SUBJECT_LENGTH + 1)
    with pytest.raises(errors.InvalidSubjectError) as excinfo:
        provider.set_to_email("test@mailgun.com").set_subject(long_subject).set_text_content("Content").send()
    assert f"Subject too long for Mailgun (max {settings.MAX_SUBJECT_LENGTH} chars)." in str(excinfo.value)

def test_mailgun_simulated_api_error():
    provider = MailgunEmailProvider()
    with pytest.raises(errors.ProviderApiError) as excinfo:
        provider.set_to_email("error@mailgun.com").set_subject("Error Test").set_text_content("Trigger API error MG").send()
    assert "Simulated Mailgun API error: invalid address" in str(excinfo.value)

def test_mailgun_simulated_internal_api_error():
    provider = MailgunEmailProvider()
    with pytest.raises(errors.ProviderApiError) as excinfo:
        provider.set_to_email("test@mailgun.com").set_subject("error_trigger_mailgun").set_text_content("Trigger internal API error MG").send()
    assert "Simulated Mailgun API error: internal issue" in str(excinfo.value)

def test_mailgun_unicode_email_and_content():
    provider = MailgunEmailProvider()
    response = provider \
        .set_to_email("user.émail@unité.com") \
        .set_subject("مرحبا from Mailgun") \
        .set_text_content("This email contains Arabic: مرحبا بالعالم") \
        .send()
    assert response["status"] == "sent"
    assert response["provider"] == "mailgun"


