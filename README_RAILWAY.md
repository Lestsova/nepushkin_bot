Railway deployment instructions (two options: GitHub or Railway CLI)

Files in this package:
- bot.py                — main bot code (reads BOT_TOKEN and CHANNEL_ID from env)
- requirements.txt      — Python deps
- .env.example          — example environment file

Quick local test:
1) unzip project
2) create virtualenv and activate:
   python3 -m venv venv
   source venv/bin/activate   (Windows: venv\Scripts\activate)
3) pip install -r requirements.txt
4) copy .env.example to .env and edit, or set env vars in your shell
5) python bot.py

Deploy to Railway (recommended: use GitHub):

Option A — via GitHub (recommended)
1) Create a GitHub repo (https://github.com/new)
2) git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
3) Go to https://railway.app, sign in with GitHub, click "New Project" -> "Deploy from GitHub repo"
4) Find your repository and deploy
5) In Railway project settings -> Variables, add:
   BOT_TOKEN = your_bot_token
   CHANNEL_ID = -1002741424126
6) Set Start Command: python bot.py
7) Deploy. Check logs — when you see "Start polling." bot is running.

Option B — Deploy from local using Railway CLI (no GitHub)
1) Install Railway CLI:
   npm install -g railway
2) Login: railway login
3) In project folder run:
   railway init
   # follow prompts to create a project
   railway up
4) In Railway dashboard, under Project -> Variables, add BOT_TOKEN and CHANNEL_ID
5) Set Start Command to: python bot.py

After deployment: open logs, make sure polling started. Test the bot in Telegram by sending /start.

Notes:
- It's recommended to set BOT_TOKEN and CHANNEL_ID as Railway environment variables (Project -> Variables).
- If you prefer the bot to read from a .env file locally, copy .env.example to .env and edit values.
