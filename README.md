# Python Email Sending Application: Refactored & Extensible

## Project Overview

This project is a refactored Python application designed for sending emails through various email service providers (ESPs). It demonstrates a clean, extensible, and testable architecture, moving from a monolithic function-based approach to a modular, object-oriented design utilizing **Abstract Base Classes (ABCs)** and the **Factory Design Pattern**. A key focus is on handling **Unicode characters** in email addresses, subjects, and content, ensuring global reach.

## Motivation and Problem Statement

The initial version of this application suffered from tight coupling, making it difficult to:
* **Test effectively:** Logic was intertwined with API calls.
* **Add new providers:** Each new ESP required modifying existing core functions.
* **Switch providers easily:** Changing the primary sending service was cumbersome.
* **Maintain agility:** Any change risked introducing regressions due to lack of modularity.

This refactoring addresses these challenges by:
1.  **Improving Testability:** Decoupling core logic from external API calls using a mocking strategy for unit tests.
2.  **Enabling Easier Development of Further Providers:** New ESPs can be integrated by implementing a defined interface.
3.  **Facilitating Easier Switching to New Providers:** A central factory allows dynamic provider selection.
4.  **Promoting Greater Agility:** The modular design reduces complexity and the risk of side effects during development.
5.  **Ensuring Unicode Support:** Robust handling of international characters in email components.

## Features

* **Multi-Provider Support:** Currently integrates with simulated SendGrid and Mailgun APIs.
* **Extensible Architecture:** Easily add new email service providers by extending a `BaseEmailProvider` abstract class.
* **Chainable API:** Fluent interface for setting email parameters (e.g., `set_to_email().set_subject().set_text_content().send()`).
* **Comprehensive Validation:** Client-side validation for email formats, subject length, and content length.
* **Custom Error Handling:** Specific exception types for clear and debuggable error reporting.
* **Mocked API Integration:** `fake_api.py` allows for fast, isolated, and reliable unit testing without hitting live services.
* **Real API Integration Option:** Configurable to send emails via actual SendGrid and Mailgun APIs.
* **Unicode Character Support:** Handles international characters in recipient/sender emails, subject, and content.

## Unicode Character Support Details

Python 3's `str` type inherently supports Unicode. This application leverages this to allow for the use of Unicode characters in:
* **Email Local Parts:** (e.g., `user.résumé@example.com`) - Characters like `é`, `ü`, `ñ`, `ç` are passed directly.
* **Email Domain Names:** (e.g., `user@méxico.com`) - While the application accepts Unicode in the domain part, true Internationalized Domain Name (IDN) support (which converts Unicode domains to Punycode, like `xn--mxico-bsa.com` for DNS resolution) is handled by the underlying email service providers (SendGrid, Mailgun) and the `requests` library (which encodes to UTF-8).
    * **Note on Dependency-Free Constraint:** Due to the project's "dependency-free" requirement (beyond standard libraries and `requests`/`pytest` for core functionality/testing), explicit **Punycode conversion** for IDNs is *not* performed within the application's validation logic. The basic email validation regex broadly checks for `@` and `.` but does not strictly enforce IDN standards. For rigorous IDN validation/conversion at the application level, a dedicated library like `idna` would typically be used.
* **Email Subjects:** (e.g., `Subject: こんにちは世界`)
* **Email Content (Plain Text & HTML):** (e.g., `Body: Привет, мир!`)

The `requests` library automatically handles the UTF-8 encoding of all string data when sending payloads to the email service APIs, ensuring Unicode characters are transmitted correctly.

## Architecture

The application is built around fundamental Object-Oriented Programming (OOP) principles and design patterns:

* **Abstract Base Class (ABC): `email_app/new/base.py`**
    * `BaseEmailProvider` defines the **contract** for any email sending service.
    * It specifies abstract methods (`_validate_input`, `_prepare_payload`, `_send_request`, `_parse_response`) that concrete providers **must** implement.
    * It also provides common, chainable setter methods (`set_to_email`, `set_subject`, etc.) and the main `send()` orchestration method.

* **Concrete Providers:**
    * `email_app/new/sendgrid_provider.py`: Implements the `BaseEmailProvider` interface for SendGrid, handling its specific payload structure, validation rules, and response parsing.
    * `email_app/new/mailgun_provider.py`: Implements the `BaseEmailProvider` interface for Mailgun, adapting to its unique requirements.

* **Factory Design Pattern: `email_app/new/factory.py`**
    * The `email_provider_factory()` function acts as a central point for creating provider instances.
    * Clients request a provider by name (e.g., `'sendgrid'`), and the factory returns the appropriate concrete class instance. This decouples client code from specific provider implementations.

* **Configuration & Error Handling:**
    * `email_app/settings.py`: Centralizes API keys (loaded securely from environment variables), API endpoints, default sender, and content limits.
    * `email_app/errors.py`: Defines custom exception classes for granular error reporting.

## Project Structure

```

email\_sending\_project/
├── email\_app/
│   ├── **init**.py           \# Makes 'email\_app' a Python package
│   ├── errors.py             \# Defines custom exception types
│   ├── settings.py           \# Stores configuration constants
│   ├── fake\_api.py           \# Simulates external email API responses
│   └── new/                  \# Contains the refactored, new application logic
│       ├── **init**.py       \# Makes 'new' a sub-package
│       ├── base.py           \# Abstract base class for email providers
│       ├── sendgrid\_provider.py  \# Concrete SendGrid implementation
│       ├── mailgun\_provider.py   \# Concrete Mailgun implementation
│       └── factory.py        \# Factory function for providers
├── test\_email\_app.py         \# Pytest test suite for verification
└── email\_demo.ipynb          \# Jupyter Notebook for interactive demo & live testing

````

## Setup and Installation

Follow these steps to get the project up and running on your local machine:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME # Navigate into your project directory
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **macOS / Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **Windows (Command Prompt):**
        ```cmd
        venv\Scripts\activate.bat
        ```
    * **Windows (PowerShell):**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
    (You'll see `(venv)` in your terminal prompt when active.)

4.  **Install Dependencies:**
    ```bash
    pip install jupyter pytest requests requests-mock
    ```

## Configuration for Real API Calls (Optional, but Recommended for Demo)

For live email sending, you'll need API keys from SendGrid and Mailgun. **Crucially, never hardcode these into your code or commit them to GitHub!** The application is designed to read them from environment variables.

1.  **Obtain API Keys:**
    * **SendGrid:** Sign up, navigate to "Settings" -> "API Keys" and create a new API Key with "Mail Send" permissions. It typically starts with `SG.`.
    * **Mailgun:** Sign up, find your "API Key" (starts with `key-`) and your "Sending Domain" (e.g., `sandbox.mailgun.org`) from your dashboard. Also note your Mailgun API base URL (e.g., `https://api.mailgun.net/v3/` for US, `https://api.eu.mailgun.net/v3/` for EU).

2.  **Set Environment Variables:**
    Set these in your terminal session *before* launching Jupyter Notebook, or directly within the `email_demo.ipynb` notebook as shown in the "Running the Application Demo" section below.

    * **macOS / Linux:**
        ```bash
        export SENDGRID_API_KEY="SG.YOUR_ACTUAL_SENDGRID_API_KEY"
        export MAILGUN_API_KEY="MG.YOUR_ACTUAL_MAILGUN_API_KEY"
        export MAILGUN_DOMAIN="your_mailgun_sending_domain.com"
        export MAILGUN_API_BASE_URL="[https://api.mailgun.net/v3/](https://api.mailgun.net/v3/)" # Adjust for EU if needed
        ```
    * **Windows (Command Prompt):**
        ```cmd
        set SENDGRID_API_KEY="SG.YOUR_ACTUAL_SENDGRID_API_KEY"
        set MAILGUN_API_KEY="MG.YOUR_ACTUAL_MAILGUN_API_KEY"
        set MAILGUN_DOMAIN="your_mailgun_sending_domain.com"
        set MAILGUN_API_BASE_URL="[https://api.mailgun.net/v3/](https://api.mailgun.net/v3/)"
        ```
    * **Windows (PowerShell):**
        ```powershell
        $env:SENDGRID_API_KEY="SG.YOUR_ACTUAL_SENDGRID_API_KEY"
        $env:MAILGUN_API_KEY="MG.YOUR_ACTUAL_MAILGUN_API_KEY"
        $env:MAILGUN_DOMAIN="your_mailgun_sending_domain.com"
        $env:MAILGUN_API_BASE_URL="[https://api.mailgun.net/v3/](https://api.mailgun.net/v3/)"
        ```

## How to Run

You can interact with this project either by running automated tests or through an interactive Jupyter Notebook demo.

### 1. Running the Automated Test Suite (Unit Tests)

This demonstrates the robust testability of the refactored code. By default, these tests use the mocked APIs for speed and isolation.

1.  **Launch Jupyter Notebook:**
    ```bash
    jupyter notebook
    ```
2.  **Open `email_demo.ipynb`** (or create a new notebook for testing, e.g., `run_tests.ipynb`).
3.  **Paste and run the following in a code cell:**
    ```python
    import sys
    import os
    import pytest # For running tests
    import importlib # For reloading modules if needed for test config

    # Add the project root to Python's path
    project_root = os.path.abspath(os.path.join(os.getcwd()))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root added to sys.path: {project_root}")

    # Ensure environment variables are set to use FAKE APIs for unit tests
    # (The pytest fixture `mock_external_api_calls_for_unit_tests` also handles this in test_email_app.py)
    os.environ["USE_FAKE_API_SENDGRID"] = "true"
    os.environ["USE_FAKE_API_MAILGUN"] = "true"
    # Also set dummy API keys to prevent `settings.py` from triggering default warning
    os.environ["SENDGRID_API_KEY"] = "SG.dummy_key_for_test"
    os.environ["MAILGUN_API_KEY"] = "MG.dummy_key_for_test"

    print("\n--- Running Pytest Unit Tests ---")
    # The '!' prefix runs the command in the shell.
    # This runs all tests discovered in 'test_email_app.py'.
    !pytest test_email_app.py

    print("\n--- Pytest run complete ---")
    ```
4.  **Observe the output:** All tests should pass, confirming the logic works as expected with the fake API.

### 2. Running the Application Demo (Interactive & Live Option)

This notebook allows you to interactively send emails, optionally using your real API keys.

1.  **Launch Jupyter Notebook:**
    ```bash
    jupyter notebook
    ```
2.  **Open `email_demo.ipynb`** (or create a new notebook).
3.  **Paste the entire demo code into a single code cell.** (The code block provided at the very end of the previous interaction, starting with `import sys` and ending with `print("Demo script finished.")`).

    * **Crucially, modify the API key placeholders and recipient email addresses within that code cell** if you want to send live emails.
    * Set `FORCE_FAKE_APIS_FOR_THIS_NOTEBOOK = False` to enable real API calls.

4.  **Run the cell.**
5.  **Observe the output:**
    * It will indicate if it's using "REAL SendGrid API" or "FAKE SendGrid API".
    * For successful sends, you'll see `SUCCESS!`.
    * For validation errors, you'll see `ERROR!` with specific messages.
6.  **Check your recipient inboxes:** If configured for real API calls and successful, you should receive the test emails.

## Demonstrated Skills

This project showcases proficiency in:

* **Object-Oriented Programming (OOP):** Class design, inheritance, abstract base classes, encapsulation.
* **Design Patterns:** Factory Pattern for flexible object creation.
* **Software Refactoring:** Transforming monolithic code into a modular, maintainable, and extensible architecture.
* **Unit Testing:** Writing isolated, reliable, and fast tests using `pytest` and mocking external dependencies (`requests-mock`).
* **API Integration:** Interacting with external RESTful APIs using the `requests` library.
* **Error Handling:** Implementing custom exceptions for clear and robust error management.
* **Configuration Management:** Securely loading sensitive data (API keys) from environment variables.
* **Unicode Handling:** Ensuring proper character encoding for international email content and addresses.
* **Version Control:** Managing project history and collaboration using Git and GitHub.
* **Interactive Development:** Using Jupyter Notebook for exploration, demonstration, and live testing.

## Future Enhancements (Optional Ideas)

* Add more email service providers (e.g., Amazon SES, SparkPost).
* Implement email templating (e.g., using Jinja2).
* Add attachment support.
* Implement asynchronous sending using `asyncio` and `httpx`.
* Build a simple command-line interface (CLI) using `argparse`.
* Add more sophisticated email address validation (e.g., leveraging `idna` for full IDN support if not dependency-free).

