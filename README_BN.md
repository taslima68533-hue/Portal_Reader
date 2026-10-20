# Portal Inbox Reader

এটি একটি বিদ্যমান Portal সার্ভিসের জন্য Flask-ভিত্তিক ওয়েব রিডার। নিজের হোস্টিংয়ে অ্যাপটি চালিয়ে আপনার নিয়ন্ত্রণে থাকা ডোমেইন যুক্ত করলে ব্যবহারকারীরা সেই ওয়েব ঠিকানা থেকে Portal inbox খুলতে পারবেন।

> **এটি শুধু inbox reader; স্বতন্ত্র mail বা sales platform নয়।** এটি Portal code তৈরি, পণ্য বিক্রি বা পেমেন্ট প্রসেস করে না। চালাতে হলে সামঞ্জস্যপূর্ণ Portal API এবং মেইলের HTML সরবরাহকারী Portal website-এ অনুমোদিত access লাগবে।

English নির্দেশনার জন্য [README.md](README.md) দেখুন।

## অ্যাপটি কী করে

- Portal-এর inbox page, mail list, preview, countdown এবং উপলব্ধ action দেখায়।
- সমর্থিত page, status, reactivate, start ও logo request Flask server-এর মাধ্যমে Portal-এ পাঠায়।
- Portal API key সার্ভারে রাখে; ব্যবহারকারীর browser-এ পাঠায় না।
- নির্ধারিত Portal website থেকে message-এর HTML নিয়ে ফেরত দেয়; Content Security Policy দিয়ে message-এর script চালানো বন্ধ রাখে।
- signed, HTTP-only browser session-এ ব্যবহারকারীর দেওয়া Portal code মনে রাখে।

অ্যাপটির নিজস্ব mail database নেই। Portal code দিয়ে সংশ্লিষ্ট inbox খোলা যায়, তাই code-কে password-এর মতো গোপন রাখুন।

## যা যা লাগবে

1. Python 3 চালাতে পারে এমন hosting—Render, অন্য Python hosting, অথবা আপনার VPS।
2. যে domain বা subdomain-এর DNS আপনি নিয়ন্ত্রণ করেন।
3. সামঞ্জস্যপূর্ণ Portal API-এর জন্য অনুমোদিত API key।
4. যে Portal website `/OTP/<code>/message/<message_id>` route চালায়, তার URL।

এই অ্যাপ নিজে থেকে যেকোনো website বা mail provider-এর সঙ্গে যুক্ত হতে পারে না। অন্য কারও Portal-এ যুক্ত হলে তাদের অনুমতি এবং আপনার ব্যবহারের জন্য ইস্যু করা API key লাগবে। API host ও website host আলাদা হতে পারে।

## সার্ভার কনফিগার করুন

Hosting dashboard-এ নিচের environment variable-গুলো সেট করুন। আসল secret public repository-তে রাখবেন না।

| Variable | লাগবে? | কাজ |
| --- | --- | --- |
| `PORTAL_API_BASE` | হ্যাঁ | Portal API-এর HTTPS base URL, শেষে `/api/v1`-সহ; যেমন `https://portal.example.com/api/v1`। |
| `PORTAL_API_KEY` | হ্যাঁ | Portal API কর্তৃক অনুমোদিত API key। গোপন রাখুন। |
| `READER_SESSION_SECRET` | হ্যাঁ | অন্তত ৩২ অক্ষরের নতুন random secret। API key বা অন্য অ্যাপের secret পুনরায় ব্যবহার করবেন না। |
| `PORTAL_WEB_BASE` | সাধারণত | message HTML সরবরাহকারী Portal website-এর HTTPS origin; যেমন `https://portal.example.com`। না দিলে অ্যাপ `PORTAL_API_BASE`-এর origin ব্যবহার করে। website-এর host আলাদা হলে এটি অবশ্যই সেট করুন। |
| `READER_COOKIE_SECURE` | production-এ হ্যাঁ | HTTPS-এ reader চালালে `true` দিন। শুধু local HTTP test-এ `false` ব্যবহার করুন। |
| `PORT` | না | Render ও অনেক hosting নিজে থেকে সেট করে। সরাসরি চালালে অ্যাপের default port `5000`। |

বিশ্বস্ত কম্পিউটারে session secret তৈরি করুন:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

এই repository-র Portal-এর জন্য আগের deployment নির্দেশনায় API base হিসেবে `https://hridoybothub.online/api/v1` দেওয়া আছে। `PORTAL_WEB_BASE`-এ সেই Portal website-এর origin দিন যেটি সত্যিই message route চালায়। API এবং website-এর host একই—এটি ধরে নেবেন না।

## Render-এ চালু করুন

1. এই repository আপনার GitHub account-এ fork করুন, অথবা deploy করার অনুমতি আছে এমন repository connect করুন।
2. Render-এ **New → Web Service** বেছে repository connect করুন।
3. Service settings দিন:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn --workers 2 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`
4. **Environment** অংশে উপরের তালিকার variable-গুলো যোগ করুন। আসল API key ও session secret সেখানে দিন, source file-এ নয়।
5. Deploy করে service URL-এর শেষে `/OTP` খুলুন।
6. নিজের domain ব্যবহার করতে Render service-এর **Custom Domains**-এ domain যোগ করুন এবং Render দেখানো DNS record সেট করুন। সাইট ব্যবহারের আগে DNS ও HTTPS চালু হওয়া পর্যন্ত অপেক্ষা করুন।

একই build ও start command সামঞ্জস্যপূর্ণ অন্য Python hosting-এও চলে। VPS-এ production web server এবং HTTPS reverse proxy-র পেছনে অ্যাপটি চালান; Flask development server সরাসরি internet-এ প্রকাশ করবেন না।

## নিজের কম্পিউটারে পরীক্ষা

Dependency ইনস্টল করুন:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Shell-এ প্রয়োজনীয় environment variable সেট করে চালান:

```bash
export PORTAL_API_BASE="https://portal.example.com/api/v1"
export PORTAL_API_KEY="your-authorized-api-key"
export READER_SESSION_SECRET="paste-a-unique-random-secret-here"
export PORTAL_WEB_BASE="https://portal.example.com"
export READER_COOKIE_SECURE="false"
python app.py
```

Windows PowerShell-এ `$env:NAME="value"` লিখে variable সেট করুন—যেমন `$env:READER_COOKIE_SECURE="false"`—তারপর `python app.py` চালান। Browser-এ `http://127.0.0.1:5000/OTP` খুলুন। Public deployment-এ HTTPS ব্যবহার করুন এবং `READER_COOKIE_SECURE=true` রাখুন।

## Request কীভাবে কাজ করে

1. ব্যবহারকারী reader খুলে Portal code দেন।
2. Reader code-টি ব্যবহারকারীর signed session cookie-তে রাখে।
3. Flask সমর্থিত request নির্ধারিত Portal API-তে পাঠায় এবং API key শুধু সার্ভার থেকে যোগ করে।
4. Message body চাইলে Flask `PORTAL_WEB_BASE`-এর সংশ্লিষ্ট message route থেকে HTML আনে এবং script বন্ধ রাখা policy-সহ browser-এ ফেরত দেয়।

সার্ভার শুধু কনফিগার করা HTTPS host ও সমর্থিত API route ব্যবহার করে। Portal code তবু inbox খোলার bearer credential: বৈধ code যার হাতে যাবে, সে inbox দেখতে পারে। Code বা API key প্রকাশ্যে দেবেন না।

## নিরাপত্তা

- `PORTAL_API_KEY` ও `READER_SESSION_SECRET` GitHub, screenshot বা log-এ রাখবেন না।
- প্রতিটি deployment-এর জন্য আলাদা random session secret ব্যবহার করুন।
- HTTPS চালু রাখুন এবং `READER_COOKIE_SECURE=true` দিন।
- API key-এর মালিকের অনুমতি ছাড়া সেটি দিয়ে deployment করবেন না।
- Secret ফাঁস হলে সেটি যেখান থেকে ইস্যু হয়েছে সেখানে revoke/rotate করে hosting-এর variable-ও বদলান।
- Inbox ও message ব্যবহারের ক্ষেত্রে Portal provider-এর নিয়ম এবং প্রযোজ্য privacy requirement মেনে চলুন।

## Project files

- `app.py` — Flask app এবং Portal proxy route।
- `templates/page.html` — reader page template।
- `requirements.txt` — Python dependency।
- `Procfile` — সামঞ্জস্যপূর্ণ hosting-এর production start command।
- `runtime.txt` — Python runtime declaration।
