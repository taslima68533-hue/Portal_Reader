# নিজের Portal Inbox Website সেটআপ

এই repository-তে Flask দিয়ে তৈরি website আছে। এটি আপনার নিয়ন্ত্রণে থাকা domain-এ চালিয়ে Portal service-এর inbox page দেখায়।

**গুরুত্বপূর্ণ:** এখানে website application-টি আছে। Portal backend, mail storage, বা Portal code তৈরি করার API নেই। সম্পূর্ণ নিজস্ব service চালাতে হলে সামঞ্জস্যপূর্ণ Portal backend ও mail system আলাদাভাবে সেটআপ করতে হবে।

English নির্দেশনার জন্য [README.md](README.md) দেখুন।

## কোন অংশ কোথায় যুক্ত হবে

| অংশ | কাজ |
| --- | --- |
| আপনার domain, যেমন `inbox.yourdomain.com` | ব্যবহারকারী এই ঠিকানায় website খুলবে। DNS এই domain-কে website চালানো VPS-এ পাঠাবে। |
| `PORTAL_API_BASE` | Website server Portal backend API থেকে inbox page ও status নেবে। এটি আপনার website domain নয়। |
| `PORTAL_WEB_BASE` | Website server আসল message HTML Portal website থেকে নেবে। API host ও website host আলাদা হতে পারে। |

শুধু domain থাকলেই Portal API বা mail service পাওয়া যায় না। Backend-কে এই project-এর প্রয়োজনীয় API route দিতে হবে এবং API key ব্যবহারের অনুমতি দিতে হবে।

## যা লাগবে

- Root বা sudo access-সহ Ubuntu/Debian VPS।
- যে domain বা subdomain-এর DNS আপনি নিয়ন্ত্রণ করেন।
- সামঞ্জস্যপূর্ণ Portal backend-এর অনুমোদিত API key।
- `/OTP/<code>/message/<message_id>` route চালায় এমন Portal website-এর HTTPS URL।

শুধু domain থাকলে এবং সম্পূর্ণ mail/Portal system নিজের করতে চাইলে, এই repository একা যথেষ্ট নয়। Backend ও mail system আলাদাভাবে সেটআপ করতে হবে।

## ১. Domain VPS-এ যুক্ত করুন

`inbox.yourdomain.com`-এর মতো একটি subdomain বেছে নিন। DNS provider-এর dashboard-এ ওই subdomain-এর জন্য VPS-এর public IP দিয়ে একটি **A record** তৈরি করুন। DNS ছড়িয়ে পড়তে কিছু সময় লাগতে পারে।

আপনার মূল website-এর DNS record পরিবর্তন করবেন না। শুধু নতুন subdomain-টি এই Flask website-এর VPS-এ যাবে।

## ২. Ubuntu/Debian VPS-এ website ইনস্টল করুন

SSH দিয়ে VPS-এ ঢুকে প্রয়োজনীয় package ইনস্টল করুন:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx
```

অ্যাপ চালানোর জন্য আলাদা system user তৈরি করে project নামান:

```bash
sudo useradd --system --home /opt/portal-website --create-home --shell /usr/sbin/nologin portalweb
sudo git clone https://github.com/taslima68533-hue/Portal_Reader.git /opt/portal-website
sudo chown -R portalweb:portalweb /opt/portal-website
sudo -u portalweb python3 -m venv /opt/portal-website/.venv
sudo -u portalweb /opt/portal-website/.venv/bin/pip install -r /opt/portal-website/requirements.txt
```

## ৩. Environment variable সেট করুন

VPS-এ private environment file তৈরি করুন:

```bash
sudo nano /etc/portal-website.env
```

নিজের আসল মানগুলো যোগ করুন:

```env
PORTAL_API_BASE=https://portal.example.com/api/v1
PORTAL_API_KEY=your-authorized-api-key
READER_SESSION_SECRET=replace-with-a-unique-random-secret
PORTAL_WEB_BASE=https://portal.example.com
READER_COOKIE_SECURE=true
PORT=8000
```

বিশ্বস্ত কম্পিউটারে নতুন random session secret তৈরি করুন:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

উদাহরণের Portal URL ও API key-এর জায়গায় অনুমোদিত Portal backend-এর আসল মান বসান। API base-এর শেষে `/api/v1` থাকতে হবে। `PORTAL_WEB_BASE`-এ message route যে website host-এ চলে সেটি দিন। Environment file-টি private রাখুন:

```bash
sudo chown root:root /etc/portal-website.env
sudo chmod 600 /etc/portal-website.env
```

আসল API key বা secret কখনো GitHub-এ রাখবেন না।

## ৪. systemd ও Gunicorn দিয়ে চালান

Service file তৈরি করুন:

```bash
sudo nano /etc/systemd/system/portal-website.service
```

এটি paste করুন:

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

Service চালু ও enable করুন:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now portal-website
sudo systemctl status portal-website
```

Gunicorn শুধু VPS-এর ভেতরের `127.0.0.1:8000` address-এ শুনবে। Nginx public request গ্রহণ করে Gunicorn-এ পাঠাবে।

## ৫. Nginx ও HTTPS সেট করুন

Nginx site configuration তৈরি করুন:

```bash
sudo nano /etc/nginx/sites-available/portal-website
```

`inbox.yourdomain.com`-এর জায়গায় নিজের subdomain বসিয়ে এই config দিন:

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

Site enable, Nginx test ও HTTPS certificate চালু করুন:

```bash
sudo ln -s /etc/nginx/sites-available/portal-website /etc/nginx/sites-enabled/portal-website
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d inbox.yourdomain.com
```

HTTPS চালু হলে `https://inbox.yourdomain.com/OTP` খুলুন। চাইলে মূল website-এ এই ঠিকানার link যোগ করুন। VPS এবং cloud firewall-এ HTTP/HTTPS-এর জন্য port 80 ও 443 খোলা থাকতে হবে।

## Website request কীভাবে কাজ করে

1. ব্যবহারকারী আপনার domain খুলে Portal code দেন।
2. Website code-টি signed, HTTP-only session cookie-তে রাখে।
3. VPS নির্ধারিত Portal API থেকে page ও status নেয়; API key শুধু সার্ভার থেকে যোগ হয়।
4. Message body চাইলে VPS `PORTAL_WEB_BASE` থেকে HTML এনে script বন্ধ রাখার policy-সহ ফেরত দেয়।

এই project নিজস্ব database-এ inbox জমা রাখে না এবং Portal code ইস্যু করে না। বৈধ Portal code দিয়ে inbox খোলা যেতে পারে, তাই code গোপন রাখুন।

## নিরাপত্তা ও রক্ষণাবেক্ষণ

- `/etc/portal-website.env` private রাখুন; GitHub-এ commit করবেন না।
- আলাদা random session secret ব্যবহার করুন এবং HTTPS website-এ `READER_COOKIE_SECURE=true` রাখুন।
- অন্য Portal operator-এর API ব্যবহার করার আগে অনুমতি নিন।
- Secret ফাঁস হলে revoke/rotate করে environment file-এ নতুন মান দিন।
- Service log দেখতে `sudo journalctl -u portal-website -f` চালান।
- Code update করার পর `sudo systemctl restart portal-website` চালান।
- Portal provider-এর শর্ত ও প্রযোজ্য privacy requirement মেনে চলুন।

## Project files

- `app.py` — Flask website ও Portal API সংযোগ।
- `templates/page.html` — HTML page template।
- `requirements.txt` — Python dependency।
- `Procfile` — সামঞ্জস্যপূর্ণ hosting-এর start command।
- `runtime.txt` — Python runtime declaration।
