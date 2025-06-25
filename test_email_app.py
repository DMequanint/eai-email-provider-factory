# test_email_app.py
# Pytest test suite to verify all functionalities of the email application.

import pytest
import os # Import os for environment variables
import requests_mock # Used for mocking HTTP requests in tests
from email_app.new.base import BaseEmailProvider
from email_app.new.sendgrid_provider import SendGridEmailProvider
from email_app.new.mailgun_provider import MailgunEmailProvider
from email_app.new.factory import email_provider_factory
from email_app import errors, settings # Import custom errors and settings for test assertions


# --- Fixture to mock HTTP requests for unit tests ---
@pytest.fixture(autouse=True)
def mock_external_api_calls_for_unit_tests(monkeypatch):
    """
    This fixture ensures unit tests always use the fake_api.py,
    regardless of actual environment variable settings for real APIs.
    It uses monkeypatch to temporarily set the environment variables during tests.
    """
    # Temporarily set environment variables to force usage of fake APIs
    monkeypatch.setenv("USE_FAKE_API_SENDGRID", "true")
    monkeypatch.setenv("USE_FAKE_API_MAILGUN", "true")

    # IMPORTANT: Also, temporarily set dummy real API keys to prevent settings.py from
    # defaulting to "DEFAULT_WARNING" which would also trigger the fake API path.
    # This ensures that if we *were* testing the real API path with requests_mock,
    # the condition `not settings.SENDGRID_API_KEY or "DEFAULT_WARNING" in settings.SENDGRID_API_KEY`
    # would evaluate correctly for real key presence.
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.dummy_key_for_test")
    monkeypatch.setenv("MAILGUN_API_KEY", "MG.dummy_key_for_test")

    # You could also use requests_mock here to mock actual HTTP calls,
    # if you were writing integration tests that explicitly hit the `requests.post` lines
    # but without connecting to a live service. For now, the `USE_FAKE_API` env var controls it.

    yield
    # Cleanup: monkeypatch automatically undoes changes after the test.


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
    provider = SendGridEmailProvider() # Use a concrete implementation for testing base methods
    chained_provider = provider \
        .set_to_email("test@example.com") \
        .set_subject("Test Subject") \
        .set_text_content("Hello World")
    
    assert chained_provider is provider # Verify chaining
    assert provider._to_email == "test@example.com"
    assert provider._subject == "Test Subject"
    assert provider._text_content == "Hello World"
    assert provider._html_content is None # Should be cleared when text is set

def test_setters_prioritize_html_over_text():
    provider = SendGridEmailProvider()
    provider.set_text_content("Plain text").set_html_content("<h1>HTML</h1>")
    assert provider._text_content is None
    assert provider._html_content == "<h1>HTML</h1>"

def test_send_without_required_fields_raises_error():
    provider = SendGridEmailProvider()
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send() # No recipient or content set
    assert "Recipient email is required." in str(excinfo.value)

    provider.set_to_email("user@example.com")
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send() # No subject or content
    assert "Subject is required." in str(excinfo.value)

    provider.set_subject("Hello")
    with pytest.raises(errors.MissingRequiredFieldError) as excinfo:
        provider.send() # No content
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

