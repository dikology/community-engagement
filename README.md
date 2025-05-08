# Community Engagement Bot

## Overview

This project implements a Telegram bot designed to foster engagement within a community. The core functionality revolves around connecting the community's primary communication platform (Telegram) with a shared knowledge base (like Google Sheets). The bot facilitates collaborative editing of the knowledge base and recognizes contributions by awarding achievements directly within Telegram.

The primary goal is to encourage the sharing and updating of valuable information relevant to community, by leveraging the familiarity of Google Sheets and the accessibility of Telegram.

## Key Features

*   **Telegram Integration:** Operates within a Telegram group, providing commands and notifications.
*   **Google Sheets Knowledge Base:** Uses a Google Sheet as a structured database for community information.
*   **Google OAuth Integration:** Securely links Telegram users to their Google accounts to reliably attribute edits made in the Google Sheet.
*   **Contribution Detection:** Utilizes Google Apps Script triggers to detect edits made to the linked Google Sheet.
*   **Webhook Communication:** Apps Script sends edit details securely to the bot's backend via webhooks.
*   **Achievement System:** Recognizes meaningful contributions (e.g., adding new entries, updating critical data) and notifies users/groups in Telegram.
*   **Dockerized Deployment:** Fully containerized using Docker and Docker Compose for consistent and scalable deployment.
*   **Production Ready:** Designed with production best practices, including secure configuration management, HTTPS support, and persistent storage.

## Technology Stack

*   **Backend Framework:** FastAPI (Python)
*   **Telegram Bot Library:** python-telegram-bot
*   **Google API Interaction:** google-api-python-client, google-auth-oauthlib
*   **Web Server:** Uvicorn
*   **Package Management:** UV
*   **Containerization:** Docker, Docker Compose
*   **Data Storage (User Mappings & OAuth State):** 
    * **User Mappings:** PostgreSQL (Recommended for structured relational data with ACID compliance)
    * **OAuth State:** Redis (Recommended for ephemeral session data with fast access and built-in expiration)
    *   *Note: Ensure the chosen storage solution is robust and handles concurrency.*
*   **Knowledge Base:** Google Sheets API
*   **Edit Detection:** Google Apps Script (Triggers & `UrlFetchApp`)
*   **Authentication:** Google OAuth 2.0 (Server-side Flow)
*   **Reverse Proxy (Recommended):** (for HTTPS termination, load balancing)

## Architecture

1.  **User Linking:**
    *   A user initiates linking via `/linkdo` in Telegram.
    *   The bot generates a unique state parameter and constructs a Google OAuth URL.
    *   The state parameter is stored temporarily (e.g., in Redis or a short-lived DB entry) associated with the Telegram User ID.
    *   The user clicks the link, authenticates with Google, and authorizes the application.
    *   Google redirects the user's browser to the bot backend's `/oauth/callback` endpoint with an authorization code and the state.
    *   The backend verifies the state against the temporary storage.
    *   The backend exchanges the authorization code for Google tokens (including an ID token).
    *   The backend verifies the ID token and extracts the user's verified Google email address.
    *   The mapping between the Telegram User ID and the Google Email is stored securely in a persistent database (e.g., PostgreSQL).
    *   The temporary state entry is deleted.
2.  **Contribution Tracking:**
    *   A linked user edits the designated Google Sheet.
    *   An `onEdit` trigger in Google Apps Script associated with the Sheet fires.
    *   The Apps Script function gathers edit details (editor's email, cell edited, new value, sheet name).
    *   The script performs basic validation (e.g., ignore header edits).
    *   The script sends a POST request (webhook) containing the edit details and a pre-shared secret to the bot backend's `/webhook/google-sheet-update` endpoint.
    *   The FastAPI backend validates the incoming webhook secret.
    *   The backend retrieves the Telegram User ID corresponding to the editor's Google Email from the persistent database.
    *   If a mapping exists, the backend evaluates the edit based on defined rules to determine if it constitutes a "meaningful contribution."
    *   If an achievement is warranted, the bot sends a notification message to the relevant Telegram user or group.

## Setup & Development

1.  **Prerequisites:** Git, Docker, Docker Compose, UV, Python 3.11+.
2.  **Clone Repository:** `git clone <your-repo-url>`
3.  **Google Cloud Project:**
    *   Set up a Google Cloud Project.
    *   Enable the "Google Sheets API".
    *   Configure the "OAuth consent screen" (External users, add required scopes: `openid`, `../auth/userinfo.email`, `../auth/userinfo.profile`). Add test users during development.
    *   Create "OAuth 2.0 Client ID" credentials (Web application).
    *   **Crucially, configure "Authorized redirect URIs".**
        *   For local development: `http://localhost:8000/oauth/callback` (or `http://127.0.0.1:8000/oauth/callback`).
        *   For production: `https://<your-domain-or-ip>/oauth/callback`.
    *   Note the `Client ID` and `Client Secret`.
4.  **Telegram Bot:** Create a bot using `@BotFather` on Telegram and note the `Bot Token`.
5.  **Google Sheet:** Create the target Google Sheet, set up the required tabs and headers. Add `Last Updated` and `Updated By` columns.
6.  **Configuration:**
    *   Copy `.env.example` to `.env`.
    *   Fill in `.env` with your Google Client ID/Secret, Telegram Bot Token, the correct `GOOGLE_REDIRECT_URI` (matching the one set in Google Cloud), your app's base URL (`APP_BASE_URL`), a secure `WEBHOOK_SECRET`, and database/Redis connection details if applicable.
7.  **Install Dependencies (Local):**
    *   `uv venv`
    *   `source .venv/bin/activate`
    *   `uv sync`
8.  **Apps Script:**
    *   Open the script editor in your Google Sheet (`Extensions` > `Apps Script`).
    *   Paste the `Code.gs` script content.
    *   Update the `webhookUrl` variable inside the script to point to your backend's webhook receiver (`https://<your-domain-or-ip>/webhook/google-sheet-update`).
    *   Update the `secret` variable inside the script to match the `WEBHOOK_SECRET` in your `.env` file.
    *   Set up an `onEdit` trigger for the script (`Triggers` > `+ Add Trigger`). Authorize the script when prompted.
9.  **Database/Cache (If Applicable):** Set up your PostgreSQL database or Redis instance according to your implementation and configure connection details in `.env`.

## Deployment (Docker Compose)

1.  **VM Setup:** Provision a VM (Yandex Cloud), install Docker and Docker Compose. Configure firewall/security groups to allow traffic on required ports (e.g., 443, 80 for HTTPS/HTTP via reverse proxy).
2.  **Clone Repository:** Clone the project onto the VM.
3.  **Create `.env` File:** Create the `.env` file on the VM with **production** values (ensure `GOOGLE_REDIRECT_URI` and `APP_BASE_URL` point to your public HTTPS domain/IP).

5.  **Build & Run:**
    *   `docker compose build`
    *   `docker compose up -d`
6.  **(Recommended) Reverse Proxy:** Set up proxy to:
    *   Handle incoming traffic on ports 80 and 443.
    *   Terminate SSL/TLS (obtain certificates via Let's Encrypt).
    *   Forward requests to the `community_bot` container (e.g., `http://community_bot:8000`).
    *   Ensure your `APP_BASE_URL` and `GOOGLE_REDIRECT_URI` use `https://`.

## Configuration Variables (`.env`)

*   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token from BotFather.
*   `GOOGLE_CLIENT_ID`: Your Google Cloud OAuth Client ID.
*   `GOOGLE_CLIENT_SECRET`: Your Google Cloud OAuth Client Secret.
*   `GOOGLE_REDIRECT_URI`: The exact HTTPS redirect URI configured in Google Cloud Credentials (e.g., `https://yourdomain.com/oauth/callback`).
*   `APP_BASE_URL`: The base HTTPS URL where your application is publicly accessible (e.g., `https://yourdomain.com`).
*   `WEBHOOK_SECRET`: A secure, randomly generated secret shared between the Apps Script and the FastAPI backend for webhook validation.
*   `DATABASE_URL`: Connection string for PostgreSQL (if used).
*   `REDIS_URL`: Connection URL for Redis (if used for state/cache).

## TODO / Future Enhancements

*   Implement more sophisticated achievement logic based on edit type/content.
*   Add commands to query the Google Sheet data directly from Telegram.
*   Implement proper async database interactions 
*   Refine error handling and user feedback messages.
*   Consider using Telegram Webhooks instead of polling for scalability.
*   Add tests.
*   Improve UI/UX for the `/link` command (e.g., Inline Keyboard Button).