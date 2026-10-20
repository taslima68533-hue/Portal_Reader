# Portal Inbox Website Setup

This repository contains a Flask website that presents inbox pages from a Portal service under a domain you control.

**Important:** this repository contains the website layer. It does not include the Portal backend, mail storage, or an API that creates Portal codes. To run a complete independent service, you must also operate or obtain authorized access to a compatible Portal backend.

বাংলা নির্দেশনার জন্য [README_BN.md](README_BN.md) দেখুন.

## How the pieces connect

There are two separate connections:

| Item | Purpose |
| --- | --- |
| Your website domain, such as `inbox.yourdomain.com` | Visitors open this address. DNS points it to the hosting service running this Flask project. |
| `PORTAL_API_BASE` | The website server requests inbox pages and status data from the Portal backend API. This is not your website domain. |
| `PORTAL_WEB_BASE` | The website server requests original message HTML from the Portal website. It can be a different host from the API. |

A domain by itself does not provide the Portal API or mail service. The backend must support the API routes used by this project, and its owner must authorize the API key.

## What you need

- A domain or subdomain whose DNS you can manage.
- A Python 3 hosting service, such as Render, or a VPS.
- An authorized API key for a compatible Portal backend.
- The HTTPS URL of the Portal website that serves `/OTP/<code>/message/<message_id>`.

If you only have a domain and want the complete mail/Portal system to be yours, this repository alone is not enough: the backend and mail system must be set up separately.

## 1. Deploy the website

On Render:

1. Fork this repository to your GitHub account.
2. In Render, select **New → Web Service** and connect your fork.
3. Set:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --workers 2 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`
4. Add the environment variables listed below in the service's **Environment** settings.
5. Deploy. The hosting provider gives you a temporary service URL. Open that URL followed by `/OTP` to check the website.

Other Python hosting can use the same build and start commands. On a VPS, run Gunicorn behind a production web server and HTTPS reverse proxy. Do not expose Flask's development server directly to the public internet.

## 2. Connect your domain

A subdomain such as `inbox.yourdomain.com` is recommended if your main website already runs elsewhere.

1. Add the subdomain in your hosting provider's custom-domain settings.
2. At your DNS provider, create the exact CNAME or A record shown by the hosting provider. DNS targets vary by host; use the values shown in your dashboard.
3. Wait for DNS verification and HTTPS certificate setup to complete.
4. Open `https://inbox.yourdomain.com/OTP`.
5. If you want visitors to find it from your main website, add a button or link there pointing to this address.

For a VPS, point an A record to the VPS public IP, then configure Nginx, Caddy, or another HTTPS reverse proxy to send requests to Gunicorn. The domain must route to this Flask service for its pages to appear.

## 3. Configure the Portal backend

Add these values in the hosting dashboard. The API base must be an actual compatible Portal API URL, not the new website's domain.

| Variable | Required | Value |
| --- | --- | --- |
| `PORTAL_API_BASE` | Yes | HTTPS API base URL ending in `/api/v1`, for example `https://portal.example.com/api/v1`. |
| `PORTAL_API_KEY` | Yes | API key issued by the Portal backend for this deployment. Keep it private. |
| `READER_SESSION_SECRET` | Yes | A unique random secret with at least 32 characters. Generate one with the command below. |
| `PORTAL_WEB_BASE` | Usually | HTTPS origin of the Portal website serving original message HTML, e.g. `https://portal.example.com`. If omitted, the app uses the origin of `PORTAL_API_BASE`. |
| `READER_COOKIE_SECURE` | Yes in production | Set to `true` for HTTPS. Use `false` only for local HTTP testing. |
| `PORT` | No | Render and many hosts set this automatically. The app uses port `5000` when run directly. |

Generate a new session secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

The API base shown in this repository's previous setup was `https://hridoybothub.online/api/v1`. Use it only if you have authorization to use that Portal. For your own backend, enter your own API URL and key. Set `PORTAL_WEB_BASE` to the host that actually serves the message route.

## How a request works

1. A visitor opens your domain and enters a Portal code.
2. The Flask website keeps the code in a signed, HTTP-only session cookie.
3. The server requests supported page/status/actions from the configured Portal API and adds the API key server-side.
4. For an email body, the server fetches HTML from `PORTAL_WEB_BASE` and sends it with a policy that blocks scripts.

This project does not store inboxes in its own database or issue Portal codes. A valid Portal code can grant access to its inbox; keep codes private.

## Local test

Install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the environment variables in the same terminal, then run the site:

```bash
export PORTAL_API_BASE="https://portal.example.com/api/v1"
export PORTAL_API_KEY="your-authorized-api-key"
export READER_SESSION_SECRET="paste-a-unique-random-secret-here"
export PORTAL_WEB_BASE="https://portal.example.com"
export READER_COOKIE_SECURE="false"
python app.py
```

On Windows PowerShell, use `$env:NAME="value"` for each variable before running `python app.py`. Open `http://127.0.0.1:5000/OTP`. For public use, configure HTTPS and set `READER_COOKIE_SECURE=true`.

## Security

- Never commit API keys or session secrets to GitHub.
- Use a different random session secret for every deployment.
- Use HTTPS for the public website.
- Obtain permission before using another Portal operator's API.
- If a key or secret leaks, revoke/rotate it and replace it in the hosting environment.
- Follow the Portal provider's terms and privacy requirements.

## Project files

- `app.py` — Flask website and API connection.
- `templates/page.html` — HTML page template.
- `requirements.txt` — Python dependencies.
- `Procfile` — production start command.
- `runtime.txt` — Python runtime declaration.
