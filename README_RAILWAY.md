Render (Web Service) deployment — webhook-ready bot

Files included:
- bot.py            # webhook-ready aiogram v2 bot (uses aiohttp via aiogram.start_webhook)
- requirements.txt  # python deps
- .env.example      # example environment file
- README_RENDER.md  # these instructions

Quick local test (optional):
1) unzip project
2) create virtualenv and install deps:
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   pip install -r requirements.txt

3) copy .env.example to .env and edit values (for local testing you can use a tunnel like ngrok for PUBLIC_URL)
   copy .env.example .env
   edit .env

4) python bot.py  (requires PUBLIC_URL reachable -> use ngrok if testing locally)

Deploy to Render (Web Service, free tier with webhook):
1) Create GitHub repo and push these files (or use existing repo).
2) In Render: New -> Web Service -> Connect GitHub repo -> choose branch main.
3) Environment variables (Service -> Environment):
   BOT_TOKEN = (your bot token from @BotFather)
   CHANNEL_ID = -1002741424126  (your channel id)
   PUBLIC_URL = https://<your-service-name>.onrender.com  (set AFTER you create the service; then redeploy)
4) Start Command: python bot.py
5) Deploy. Check Logs -> when you see "Webhook set to https://..." bot is ready. Test by sending /start

Notes:
- PUBLIC_URL must be your Render service URL (https://your-app.onrender.com). Set it in Environment variables and redeploy so the bot sets webhook correctly.
- If you use GitHub, Render will redeploy automatically on push to main branch.
- For webhook mode make sure the service uses HTTPS (Render provides it automatically).
