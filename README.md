# Portal Inbox Reader (Render Ready)

আপনার নিজস্ব ডোমেইনে মূল Portal-এর একই পেজ, লোগো, মেইল লিস্ট, প্রিভিউ, কাউন্টডাউন, Copy, New Mail, Reactivate ও Buy Again দেখাবে।

এটি ইনবক্স রিডার। নতুন কোড কেনা বা টাকা কাটার কোনো সিস্টেম এই প্রজেক্টে নেই। ব্যবহারকারী আগে কেনা Portal কোড ইনপুট করবেন।

## Render-এ Deploy করার উপায় (সবচেয়ে সহজ)

1. এই ফোল্ডারটি GitHub-এ push করুন (অথবা Render-এ সরাসরি upload করুন যদি সাপোর্ট করে)।

2. [render.com](https://render.com) এ গিয়ে **New + → Web Service** সিলেক্ট করুন।

3. আপনার GitHub repo connect করুন।

4. Settings:

   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --workers 2 --threads 4 --timeout 30 --bind 0.0.0.0:$PORT app:app`  
     (অথবা Procfile থাকলে অটোমেটিক নিবে)
   - **Instance Type**: Free বা Starter

5. **Environment Variables** সেট করুন (Dashboard → Environment):

   | Key | Value |
   |-----|-------|
   | `PORTAL_API_BASE` | `https://hridoybothub.online/api/v1` |
   | `PORTAL_API_KEY` | আপনার নিজের API key (Telegram bot থেকে `/apikey` দিয়ে নিন) |
   | `READER_SESSION_SECRET` | কমপক্ষে ৩২ ক্যারেক্টারের random secret (নিচে কমান্ড দেখুন) |
   | `READER_COOKIE_SECURE` | `true` |
   | `PORT` | (Render অটোমেটিক দেয়, সেট না করলেও চলবে) |

   Random secret তৈরি করতে আপনার কম্পিউটারে চালান:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

6. Deploy করুন। কয়েক মিনিট পর আপনার Render URL-এ `/OTP` খুলুন।

7. Custom domain চাইলে Render Dashboard থেকে Add Custom Domain করুন এবং DNS সেট করুন।

## লোকালে টেস্ট করতে

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env এ API key ও secret বসান
export READER_COOKIE_SECURE=false
gunicorn --workers 1 --bind 127.0.0.1:5000 app:app
```

তারপর `http://127.0.0.1:5000/OTP` খুলুন।

## গুরুত্বপূর্ণ নোট

- API key শুধু সার্ভারে থাকবে। ব্রাউজারে যাবে না।
- Portal Code জানা থাকলে ইনবক্স খোলা যায় — কোড গোপন রাখুন।
- Free tier-এ কয়েক মিনিট inactivity-র পর sleep হতে পারে। Production-এ Starter plan ব্যবহার করুন।
- সবকিছু HTTPS-এ চলবে।

---

**English summary**: Ready-to-deploy Flask app for Render. Set the 3 environment variables above and deploy. Open `/OTP` on your Render URL.
