# Portal Inbox Reader

A Flask web reader for an existing Portal service. Deploy it on your own hosting and connect a domain you control to give users a separate web address for opening their Portal inboxes.

> **This is a reader, not a standalone mail or sales platform.** It does not create Portal codes, sell products, or process payments. It needs access to a compatible Portal API and the Portal website that serves message HTML.

বাংলা নির্দেশনার জন্য [README_BN.md](README_BN.md) দেখুন।

## What it does

- Displays the Portal's inbox page, mail list, previews, countdown, and available actions.
- Proxies supported page, status, reactivate, start, and logo requests through the Flask server.
- Keeps the Portal API key on the server; it is not sent to the visitor's browser.
- Fetches a message's HTML from the configured Portal website and serves it with a Content Security Policy that blocks scripts.
- Uses a signed, HTTP-only browser session to remember Portal codes entered by a visitor.

The app does not have its own mail database. Portal codes grant access to the corresponding inbox, so treat them like passwords.

## Requirements

You need:

1. A Python 3 service (Render, another Python host, or your own VPS).
2. A domain or subdomain whose DNS you can manage.
3. A valid API key for a compatible Portal API.
4. The Portal website URL that serves `/OTP/<code>/message/<message_id>`.

This app cannot connect to an arbitrary website or mail provider by itself. If you are connecting to someone else's Portal, you need their authorization and an API key issued for your use. The API host and website host may be different.

## Configure the service

Set these environment variables in your hosting dashboard. Do not put real secrets in this public repository.

| Variable | Required | Description |
| --- | --- | --- |
| `PORTAL_API_BASE` | Yes | HTTPS base URL of the Portal API, including `/api/v1`; for example, `https://portal.example.com/api/v1`. |
| `PORTAL_API_KEY` | Yes | API key authorized by the Portal API. Keep it private. |
| `READER_SESSION_SECRET` | Yes | A unique random secret of at least 32 characters. Do not reuse the API key or a secret from another app. |
| `PORTAL_WEB_BASE` | Usually | HTTPS origin of the Portal website that serves message HTML, for example `https://portal.example.com`. If omitted, the app uses the origin from `PORTAL_API_BASE`. Set it explicitly if the Portal website uses a different host. |
| `READER_COOKIE_SECURE` | Yes in production | Set to `true` when the reader is served over HTTPS. Use `false` only for local HTTP testing. |
| `PORT` | No | Set automatically by Render and many other hosts. The app defaults to port `5000` when run directly. |

Generate a session secret on a trusted computer:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

For this repository's Portal, the API base shown in the existing deployment guide is `https://hridoybothub.online/api/v1`. Use the Portal website origin that actually serves the message route for `PORTAL_WEB_BASE`; do not assume the API and website hosts are always identical.

## Deploy on Render

1. Fork this repository to your GitHub account, or connect a repository you are authorized to deploy.
2. In Render, choose **New → Web Service** and connect the repository.
3. Configure the service:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --workers 2 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`
4. In **Environment**, add the variables from the table above. Paste the real API key and session secret there, not into a source file.
5. Deploy and open the service URL followed by `/OTP`.
6. To use your own domain, add it under the Render service's **Custom Domains** settings and follow the DNS records Render provides. Wait for DNS and HTTPS provisioning to finish before using the site.

The same build and start commands work on compatible Python hosting. For a VPS, run the app behind a production web server and an HTTPS reverse proxy; do not expose Flask's development server directly to the internet.

## Local test

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the required environment variables in your shell, then run:

```bash
export PORTAL_API_BASE="https://portal.example.com/api/v1"
export PORTAL_API_KEY="your-authorized-api-key"
export READER_SESSION_SECRET="paste-a-unique-random-secret-here"
export PORTAL_WEB_BASE="https://portal.example.com"
export READER_COOKIE_SECURE="false"
python app.py
```

On Windows PowerShell, set them with `$env:NAME="value"` (for example, `$env:READER_COOKIE_SECURE="false"`) before running `python app.py`. Open `http://127.0.0.1:5000/OTP`. Use HTTPS and set `READER_COOKIE_SECURE=true` for a public deployment.

## Request flow

1. A visitor opens the reader and enters a Portal code.
2. The reader stores that code in the visitor's signed session cookie.
3. Flask sends supported requests to the configured Portal API. The API key is added server-side.
4. For a message body, Flask requests the corresponding message route from `PORTAL_WEB_BASE` and returns the HTML with a restrictive policy that blocks scripts.

The server accepts only configured HTTPS hosts and supported API routes. A Portal code is still a bearer credential: anyone who obtains a valid code may be able to open its inbox. Do not share codes or API keys publicly.

## Security checklist

- Keep `PORTAL_API_KEY` and `READER_SESSION_SECRET` out of GitHub, screenshots, and logs.
- Use a different, randomly generated session secret for every deployment.
- Serve the reader over HTTPS and keep `READER_COOKIE_SECURE=true`.
- Do not deploy with an API key unless its owner has authorized that use.
- If a secret is exposed, revoke or rotate it at its issuer and update the hosting environment.
- Follow the Portal provider's rules and applicable privacy requirements when handling inboxes and messages.

## Project files

- `app.py` — Flask application and Portal proxy routes.
- `templates/page.html` — reader page template.
- `requirements.txt` — Python dependencies.
- `Procfile` — production start command for compatible hosts.
- `runtime.txt` — Python runtime declaration.
