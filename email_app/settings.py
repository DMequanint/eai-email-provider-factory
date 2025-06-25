# email_app/settings.py
# Author: Dessalegn Mequanint Yehuala
# Date: June, 2025
# Description: Stores configuration constants for the email application.

import os

# --- API Keys (LOAD FROM ENVIRONMENT VARIABLES FOR SECURITY) ---
# For a real application, NEVER hardcode API keys. Use environment variables.
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "SG.mock_sendgrid_api_key_12345_DEFAULT_WARNING")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "MG.mock_mailgun_api_key_67890_DEFAULT_WARNING")

# --- API Endpoints ---
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
# For Mailgun, the API URL depends on the domain and region.
# Example for EU region: "https://api.eu.mailgun.net/v3/"
# Example for US region: "https://api.mailgun.net/v3/"
MAILGUN_API_BASE_URL = os.getenv("MAILGUN_API_BASE_URL", "https://api.mailgun.net/v3/")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "sandbox.mailgun.org") # Your Mailgun sending domain

# --- Default Sender and Max Lengths ---
DEFAULT_SENDER_EMAIL = "noreply@example.com"

MAX_EMAIL_ADDRESS_LENGTH = 254
MAX_SUBJECT_LENGTH = 255
MAX_TEXT_CONTENT_LENGTH = 10000
MAX_HTML_CONTENT_LENGTH = 50000


