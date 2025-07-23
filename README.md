-----

# ROAMGENIE

*Empowering Seamless Automation for Limitless Possibilities*

[](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/Arisha-27/roamgeni) [](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/Arisha-27/roamgeni) [](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/Arisha-27/roamgeni) [](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/Arisha-27/roamgeni)

Built with the tools and technologies:

  

-----

## Table of Contents

  * [Overview](https://www.google.com/search?q=%23overview)
  * [Getting Started](https://www.google.com/search?q=%23getting-started)
      * [Prerequisites](https://www.google.com/search?q=%23prerequisites)
      * [Installation](https://www.google.com/search?q=%23installation)
      * [Configuration](https://www.google.com/search?q=%23configuration)
      * [Usage](https://www.google.com/search?q=%23usage)
  * [API Endpoints (IVR Server)](https://www.google.com/search?q=%23api-endpoints-ivr-server)
  * [Project Structure](https://www.google.com/search?q=%23project-structure)
  * [Dependencies](https://www.google.com/search?q=%23dependencies)
  * [Testing](https://www.google.com/search?q=%23testing)
  * [Return](https://www.google.com/search?q=%23return)

-----

## Overview

Roamgenie is an AI travel agent designed as a powerful developer tool for orchestrating complex automation and data processing workflows. It seamlessly integrates web scraping, text extraction, and communication systems to enable intelligent decision-making and operational efficiency for travelers. This project empowers developers to build scalable, automated solutions with ease, focusing on enhancing customer interactions and supporting travel data management through advanced AI agents and communication workflows.

Roamgeni's core features include:

1. AI Travel Companion Agent (ATCA): Provides real-time itinerary updates, booking tracking, and offers support through WhatsApp, web, or mobile interfaces. It also handles emergency information and offline fallback scenarios.

2. AI Inquiry Call Agent (AICA): A multilingual IVR voice bot designed to assist with bookings, refunds, and escalations.


3. Search & Data Retrieval: Utilizes SerpApi for efficient search data collection, crucial for finding flights and other travel-related information.


4. Text & Document Analysis: Implements OCR for extracting information from images and documents, such as passport scans.


5. Communication Workflows: Integrates Twilio for notifications and IVR systems to enhance customer interactions, supporting features like IVR calls and emergency alerts.


6. Orchestration Hub: Acts as the central coordinator for data acquisition, processing, and alerts.


7. Travel & Customer Support: Supports travel data management and multilingual customer service solutions.

8. Passport Scan: Integrates functionality for uploading and scanning passport photos to discover visa-free travel destinations.

9. Emergency & Offline Support: Features simulation for flight cancellation alerts and offline fallback messages via WhatsApp.

10. CRM Integration: Provides a contact form to save user information into a CRM system (Vendasta in this case)

-----

## Getting Started

### Prerequisites

This project requires the following dependencies:

  * **Programming Language:** Python
  * **Package Manager:** Pip
  * **External APIs:**
      * [SerpApi Key](https://serpapi.com/) for Google Search and Google Flights data.
      * [Google API Key](https://console.cloud.google.com/apis/credentials) with access to Google Gemini (Generative Language API) for AI Agent functionalities.
      * [Twilio Account SID, Auth Token, and Phone Number](https://www.twilio.com/) for voice calls and WhatsApp messages.
      * [Ngrok](https://ngrok.com/) (or similar tunneling service) to expose your local FastAPI IVR server to the internet for Twilio webhooks.

### Installation

Build roamgenie from the source and install dependencies:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Arisha-27/roamgeni
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd roamgeni
    ```

3.  **Install the dependencies:**

    Using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

    [cite\_start]The key dependencies installed are `streamlit`, `serpapi`, and `agno`. [cite: 1]

### Configuration

Before running the application, you need to configure your API keys and secrets.

1.  **Create `.streamlit` directory:** In the root of your project directory, create a folder named `.streamlit`.

    ```bash
    mkdir .streamlit
    ```

2.  **Create `secrets.toml`:** Inside the `.streamlit` directory, create a file named `secrets.toml`.

    ```bash
    touch .streamlit/secrets.toml
    ```

3.  **Add your secrets to `secrets.toml`:**

    ```toml
    # .streamlit/secrets.toml
    TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Your Twilio Account SID
    TWILIO_AUTH_TOKEN = "your_twilio_auth_token"          # Your Twilio Auth Token
    TWILIO_PHONE_NUMBER = "+1234567890"                   # Your Twilio Phone Number (e.g., +1XXXXXXXXXX)
    TWILIO_WHATSAPP = "whatsapp:+14155238886"             # Your Twilio WhatsApp Sandbox number (or actual WhatsApp number)

    SERPAPI_KEY = "your_serpapi_api_key"                  # Your SerpApi API Key
    GOOGLE_API_KEY = "your_google_gemini_api_key"         # Your Google Gemini API Key (ensure Generative Language API is enabled)
    ```

    *Replace placeholder values with your actual API keys and numbers.*

4.  **Configure `ivr_server.py`:**
    Open `ivr_server.py` and update the following variables with your actual Twilio credentials and Ngrok URL:

    ```python
    # ivr_server.py
    BASE_URL = "YOUR_NGROK_URL"  # e.g., "https://abcdef123456.ngrok.io"
    TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Your Twilio Account SID
    TWILIO_AUTH_TOKEN = "your_twilio_auth_token"          # Your Twilio Auth Token
    TWILIO_NUMBER = "+1234567890"                       # Your Twilio Phone Number
    ```

    *Ensure `BASE_URL` is updated every time your Ngrok URL changes.*

### Usage

This project involves two main components: a Streamlit frontend and a FastAPI backend for IVR calls. Both need to be running concurrently for full functionality.

1.  **Start the FastAPI IVR Server:**
    Open a terminal, navigate to your project directory, and run:

    ```bash
    python ivr_server.py
    ```

    This will start the FastAPI server, usually on `http://0.0.0.0:8010`.

2.  **Expose the FastAPI server using Ngrok:**
    Open another terminal and run Ngrok to create a public URL for your FastAPI server.

    ```bash
    ngrok http 8010
    ```

    Copy the `https://` forwarding URL provided by Ngrok (e.g., `https://abcdef123456.ngrok.io`). This is your `BASE_URL` for `ivr_server.py` and `FASTAPI_IVR_URL` for `source.py`. **Make sure to update the `BASE_URL` variable in `ivr_server.py` AND the `FASTAPI_IVR_URL` in `source.py` with this Ngrok URL.**

3.  **Start the Streamlit Frontend:**
    Open a third terminal, navigate to your project directory, and run:

    ```bash
    streamlit run source.py
    ```

    Your Streamlit application will open in your web browser.

4.  **Configure Twilio Webhooks:**
    For the IVR call functionality to work, you must configure your Twilio phone number to point to your Ngrok URL.

      * Go to your [Twilio Console](https://www.twilio.com/console/phone-numbers/incoming).
      * Select your active Twilio Phone Number.
      * Under the "Voice & Fax" section, for "A CALL COMES IN", select "Webhook" and enter your Ngrok URL followed by `/ivr-language` (e.g., `https://abcdef123456.ngrok.io/ivr-language`). Set the method to `HTTP POST`.
      * Save your changes.

-----

## API Endpoints (IVR Server)

The `ivr_server.py` provides the following FastAPI endpoints for the Interactive Voice Response system:

  * **`/` (GET):** Root endpoint, returns a simple "Travel Agent IVR Service is running" message for health check.
  * **`/health` (GET):** Returns `{"status": "healthy", "service": "Travel Agent IVR"}`.
  * **`/start-call` (POST):** Initiates a voice call to the `to_number` provided in the request body.
      * **Request Body:** `{"to_number": "+91XXXXXXXXXX"}`
      * **Response:** `{"success": true, "sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}` or error details.
  * **`/ivr-language` (POST):** Twilio webhook endpoint for initial call, prompts for language selection (English/Hindi).
  * **`/ivr-menu` (POST):** Handles language selection and directs to respective language options.
  * **`/ivr-english-options` (POST):** Presents options for booking, refund, or escalation in English.
  * **`/ivr-hindi-options` (POST):** Presents options for booking, refund, or escalation in Hindi.

-----

## Project Structure

The key files in this project include:

  * `source.py`: The main Streamlit frontend application.
  * `ivr_server.py`: The FastAPI backend for handling Twilio IVR webhooks.
  * [cite\_start]`requirements.txt`: Lists all Python dependencies. [cite: 1]
  * `.streamlit/secrets.toml`: Stores sensitive API keys and credentials (not committed to version control).
  * `Roamlogo.png`: Project logo.
  * `visa_data.json`: Example JSON dataset for visa requirements.

-----

## Dependencies

[cite\_start]The project's dependencies are listed in `requirements.txt`: [cite: 1]

  * [cite\_start]`streamlit>=1.30.0` [cite: 1]
  * [cite\_start]`serpapi>=0.1.4` [cite: 1]
  * [cite\_start]`agno>=0.1.8` [cite: 1]
  * [cite\_start]`python-dotenv>=1.0.1` (Note: While `python-dotenv` is in `requirements.txt`, Streamlit's `st.secrets` is typically used for secret management in Streamlit Cloud deployments, which abstracts away `.env` files.) [cite: 1]
  * `pandas`
  * `Pillow` (PIL)
  * `opencv-python` (cv2)
  * `numpy`
  * `pytesseract`
  * `twilio`
  * `fastapi`
  * `uvicorn`
  * `pydantic` (a dependency of FastAPI)

-----

## Testing

*(Note: The provided information for testing is generic. Replace `{test_framework}` with the actual framework, e.g., `pytest`.)*

Roamgeni uses the `{test_framework}` test framework. Run the test suite with:

Using `pip`:

```bash
pytest
```

-----

[Return](https://www.google.com/search?q=%23table-of-contents)

-----
