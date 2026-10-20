# Portal Inbox Website Setup

This repository contains a Flask website that displays inbox pages from a Portal service under a domain you control.

**Important:** this repository contains the website application only. It does not include the Portal backend, mail storage, or an API that creates Portal codes. A complete independent service also needs a compatible Portal backend and mail system.

বাংলা নির্দেশনার জন্য [README_BN.md](README_BN.md) দেখুন.

## What connects to what

| Item | Purpose |
| --- | --- |
| Your domain, e.g. `inbox.yourdomain.com` | Visitors open this address. DNS points it to the VPS running this website. |
| `PORTAL_API_BASE` | The website server requests inbox pages and status from the Portal backend API. This is not your website domain. |
| `PORTAL_WEB_BASE` | The website server requests original message HTML from the Portal website. It may be a different host from the API. |

A domain alone does not provide a Portal API or mail service. The backend must support the API routes used by this project, and its owner must authorize the API key.

## Requirements

- An Ubuntu or Debian VPS with root or sudo access.
- A domain or subdomain whose DNS you can manage.
- An authorized API key for a compatible Portal backend.
- The HTTPS URL of the Portal website that serves `/OTP/<code>/message/<message_id>`.

If you only have a domain and want the complete mail/Portal system to be yours, this repository alone is not enough. The backend and mail system must be set up separately.

## 1. Point your domain to the VPS

Choose a subdomain such as `inbox.yourdomain.com`. At your DNS provider, create an **A record** for that subdomain pointing to your VPS public IP address. DNS changes can take time to propagate.

Keep your main website's existing DNS records unchanged. The subdomain will point to this Flask website.

## 2. Install the website on Ubuntu/Debian

Connect to your VPS over SSH, then install the required system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx
```

Create a dedicated system account and download the project:

```bash
sudo useradd --system --home /opt/portal-website --create-home --shell /usr/sbin/nologin portalweb
sudo git clone https://github.com/taslima68533-hue/Portal_Reader.git /opt/portal-website
sudo chown -R portalweb:portalweb /opt/portal-website
sudo -u portalweb python3 -m venv /opt/portal-website/.venv
sudo -u portalweb /opt/portal-website/.venv/bin/pip install -r /opt/portal-website/requirements.txt
```

## 3. Set the environment variables

Create a private environment file on the VPS:

```bash
sudo nano /etc/portal-website.env
```

Add your own values:

```env
PORTAL_API_BASE=https://portal.example.com/api/v1
PORTAL_API_KEY=your-authorized-api-key
READER_SESSION_SECRET=replace-with-a-unique-random-secret
PORTAL_WEB_BASE=https://portal.example.com
READER_COOKIE_SECURE=true
PORT=8000
```

Generate a random session secret on a trusted computer:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Replace the example Portal URLs and API key with the real values for a Portal backend you are authorized to use. The API base must end in `/api/v1`. `PORTAL_WEB_BASE` must be the website host that actually serves the message route. Lock down the environment file:

```bash
sudo chown root:root /etc/portal-website.env
sudo chmod 600 /etc/portal-website.env
```

Never put real API keys or secrets in GitHub.

## 4. Run the app with systemd and Gunicorn

Create the service file:

```bash
sudo nano /etc/systemd/system/portal-website.service
```

Paste:

```ini
[Unit]
Description=Portal Inbox Website
After=network.target

[Service]
User=portalweb
Group=portalweb
WorkingDirectory=/opt/portal-website
EnvironmentFile=/etc/portal-website.env
ExecStart=/opt/portal-website/.venv/bin/gunicorn --workers 2 --threads 4 --timeout 30 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now portal-website
sudo systemctl status portal-website
```

Gunicorn listens only on the VPS itself at `127.0.0.1:8000`. Nginx will receive public web requests and forward them to Gunicorn.

## 5. Configure Nginx and HTTPS

Create an Nginx site configuration:

```bash
sudo nano /etc/nginx/sites-available/portal-website
```

Replace `inbox.yourdomain.com` with your subdomain:

```nginx
server {
    listen 80;
    server_name inbox.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site, test Nginx, and request a free HTTPS certificate:

```bash
sudo ln -s /etc/nginx/sites-available/portal-website /etc/nginx/sites-enabled/portal-website
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d inbox.yourdomain.com
```

After HTTPS is active, open `https://inbox.yourdomain.com/OTP`. You can add a link to this address from your main website.

## How requests work

1. A visitor opens your domain and enters a Portal code.
2. The website keeps the code in a signed, HTTP-only session cookie.
3. The VPS requests supported pages and status from the configured Portal API; the API key is added server-side.
4. For a message body, the VPS fetches HTML from `PORTAL_WEB_BASE` and returns it with a policy that blocks scripts.

This project does not store inboxes in its own database or issue Portal codes. A valid Portal code can grant access to its inbox, so keep codes private.

## Security and maintenance

- Keep `/etc/portal-website.env` private; do not commit it to GitHub.
- Use a unique random session secret and keep `READER_COOKIE_SECURE=true` on the HTTPS site.
- Obtain permission before using another Portal operator's API key.
- If a secret is exposed, revoke or rotate it and update the environment file.
- Check service logs with `sudo journalctl -u portal-website -f`.
- After updating code, restart the service with `sudo systemctl restart portal-website`.
- Follow the Portal provider's terms and applicable privacy requirements.

## Project files

- `app.py` — Flask website and Portal API connection.
- `templates/page.html` — HTML page template.
- `requirements.txt` — Python dependencies.
- `Procfile` — start command for compatible hosting.
- `runtime.txt` — Python runtime declaration.
