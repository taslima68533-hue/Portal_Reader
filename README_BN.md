# নিজের Portal Inbox Website সেটআপ

এই repository-তে Flask দিয়ে তৈরি একটি website আছে। এটি আপনার নিয়ন্ত্রণে থাকা domain-এ চালিয়ে Portal service-এর inbox page দেখায়।

**গুরুত্বপূর্ণ:** এই repository-তে website-এর অংশটি আছে। Portal backend, mail storage, বা Portal code তৈরি করার API এতে নেই। সম্পূর্ণ আলাদা service চালাতে হলে সামঞ্জস্যপূর্ণ Portal backend নিজে চালাতে হবে, অথবা অনুমোদিত access নিতে হবে।

English নির্দেশনার জন্য [README.md](README.md) দেখুন.

## কোন অংশ কীসের সঙ্গে যুক্ত

এখানে দুটি আলাদা সংযোগ আছে:

| অংশ | কাজ |
| --- | --- |
| আপনার website domain, যেমন `inbox.yourdomain.com` | ব্যবহারকারী এই ঠিকানায় website খুলবে। DNS এই domain-কে Flask project চালানো hosting-এ পাঠাবে। |
| `PORTAL_API_BASE` | Website server inbox page ও status-এর তথ্য Portal backend API থেকে আনবে। এটি আপনার website domain নয়। |
| `PORTAL_WEB_BASE` | Website server আসল message HTML Portal website থেকে আনবে। API host ও website host আলাদা হতে পারে। |

শুধু domain থাকলেই Portal API বা mail service পাওয়া যায় না। Backend-কে এই project-এর প্রয়োজনীয় API route সমর্থন করতে হবে এবং API key ব্যবহারের অনুমতি দিতে হবে।

## যা লাগবে

- যে domain বা subdomain-এর DNS আপনি নিয়ন্ত্রণ করেন।
- Python 3 চালাতে পারে এমন hosting—যেমন Render বা VPS।
- সামঞ্জস্যপূর্ণ Portal backend-এর অনুমোদিত API key।
- `/OTP/<code>/message/<message_id>` route চালায় এমন Portal website-এর HTTPS URL।

আপনার যদি শুধু domain থাকে এবং সম্পূর্ণ mail/Portal system নিজের করতে চান, এই repository একা যথেষ্ট নয়—backend ও mail system আলাদাভাবে সেটআপ করতে হবে।

## ১. Website deploy করুন

Render-এ:

1. Repository-টি আপনার GitHub account-এ fork করুন।
2. Render-এ **New → Web Service** বেছে fork করা repository connect করুন।
3. সেটিংস দিন:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --workers 2 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`
4. Service-এর **Environment** settings-এ নিচে দেওয়া variable-গুলো যোগ করুন।
5. Deploy করুন। Hosting একটি অস্থায়ী service URL দেবে। Website পরীক্ষা করতে URL-এর শেষে `/OTP` খুলুন।

অন্য Python hosting-এও একই build ও start command ব্যবহার করা যায়। VPS-এ Gunicorn-কে production web server ও HTTPS reverse proxy-র পেছনে চালান। Flask development server সরাসরি public internet-এ প্রকাশ করবেন না।

## ২. নিজের domain যুক্ত করুন

আপনার মূল website আগে থেকেই অন্য hosting-এ থাকলে `inbox.yourdomain.com`-এর মতো আলাদা subdomain ব্যবহার করা সুবিধাজনক।

1. Hosting provider-এর custom-domain settings-এ subdomain যোগ করুন।
2. DNS provider-এর dashboard-এ hosting provider দেখানো CNAME বা A record বসান। DNS-এর মান hosting অনুযায়ী আলাদা হয়—আপনার dashboard-এ দেখানো মানই ব্যবহার করুন।
3. DNS যাচাই ও HTTPS certificate চালু হওয়া পর্যন্ত অপেক্ষা করুন।
4. `https://inbox.yourdomain.com/OTP` খুলুন।
5. মূল website থেকেও ব্যবহারকারীদের পাঠাতে চাইলে সেখানে এই ঠিকানার button বা link যোগ করুন।

VPS হলে domain-এর A record VPS-এর public IP-তে দিন। এরপর Nginx, Caddy বা অন্য HTTPS reverse proxy এমনভাবে সেট করুন যেন request Gunicorn-এ যায়। Website দেখাতে domain-টিকে এই Flask service-এ route করতে হবে।

## ৩. Portal backend-এর সংযোগ সেট করুন

Hosting dashboard-এ নিচের variable-গুলো দিন। API base-এ সামঞ্জস্যপূর্ণ Portal API-এর আসল URL বসবে; নতুন website-এর domain নয়।

| Variable | লাগবে? | কী বসবে |
| --- | --- | --- |
| `PORTAL_API_BASE` | হ্যাঁ | HTTPS API base URL, শেষে `/api/v1`-সহ; যেমন `https://portal.example.com/api/v1`। |
| `PORTAL_API_KEY` | হ্যাঁ | এই deployment-এর জন্য Portal backend থেকে পাওয়া API key। গোপন রাখুন। |
| `READER_SESSION_SECRET` | হ্যাঁ | অন্তত ৩২ অক্ষরের আলাদা random secret। নিচের command দিয়ে তৈরি করুন। |
| `PORTAL_WEB_BASE` | সাধারণত | আসল message HTML দেওয়া Portal website-এর HTTPS origin; যেমন `https://portal.example.com`। না দিলে অ্যাপ `PORTAL_API_BASE`-এর origin নেয়। |
| `READER_COOKIE_SECURE` | production-এ হ্যাঁ | HTTPS হলে `true` দিন। শুধু local HTTP test-এ `false` ব্যবহার করুন। |
| `PORT` | না | Render ও অনেক hosting নিজে থেকে সেট করে। সরাসরি চালালে app-এর default port `5000`। |

নতুন session secret তৈরি করুন:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

এই repository-র আগের setup-এ API base হিসেবে `https://hridoybothub.online/api/v1` দেওয়া ছিল। ওই Portal ব্যবহারের অনুমতি থাকলেই এটি ব্যবহার করুন। নিজের backend হলে নিজের API URL ও key বসান। `PORTAL_WEB_BASE`-এ message route যে host-এ চলে, সেই host দিন।

## Website-এ request কীভাবে চলে

1. ব্যবহারকারী আপনার domain খুলে Portal code দেন।
2. Flask website code-টি signed, HTTP-only session cookie-তে রাখে।
3. Server নির্ধারিত Portal API-তে page/status/action-এর request পাঠায় এবং API key শুধু server থেকেই যোগ করে।
4. Mail body দেখানোর জন্য server `PORTAL_WEB_BASE` থেকে HTML আনে এবং script বন্ধ রাখার policy-সহ ফেরত দেয়।

এই project নিজস্ব database-এ inbox সংরক্ষণ করে না এবং Portal code ইস্যু করে না। বৈধ Portal code দিয়ে তার inbox খোলা যেতে পারে, তাই code গোপন রাখুন।

## নিজের কম্পিউটারে পরীক্ষা

Dependency ইনস্টল করুন:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

একই terminal-এ environment variable সেট করে website চালান:

```bash
export PORTAL_API_BASE="https://portal.example.com/api/v1"
export PORTAL_API_KEY="your-authorized-api-key"
export READER_SESSION_SECRET="paste-a-unique-random-secret-here"
export PORTAL_WEB_BASE="https://portal.example.com"
export READER_COOKIE_SECURE="false"
python app.py
```

Windows PowerShell-এ `$env:NAME="value"` ব্যবহার করে variable-গুলো সেট করে `python app.py` চালান। Browser-এ `http://127.0.0.1:5000/OTP` খুলুন। Public website-এ HTTPS চালু করে `READER_COOKIE_SECURE=true` রাখুন।

## নিরাপত্তা

- API key বা session secret GitHub-এ commit করবেন না।
- প্রতিটি deployment-এর জন্য আলাদা random session secret ব্যবহার করুন।
- Public website-এ HTTPS ব্যবহার করুন।
- অন্য Portal operator-এর API ব্যবহার করার আগে অনুমতি নিন।
- API key বা secret ফাঁস হলে issuer-এর কাছে revoke/rotate করে hosting-এর variable-ও বদলান।
- Portal provider-এর শর্ত এবং প্রযোজ্য privacy requirement মেনে চলুন।

## Project files

- `app.py` — Flask website এবং API সংযোগ।
- `templates/page.html` — HTML page template।
- `requirements.txt` — Python dependencies।
- `Procfile` — production start command।
- `runtime.txt` — Python runtime declaration।
