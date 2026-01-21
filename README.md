# FadMann

**Reconnect with your campus community, one message at a time.**

---

## Why I Built This

FadMann started from something I noticed during my first year: as our campus got bigger and everyone's schedules got busier, we were all losing touch with each other. I'd see people I knew from classes in the dining hall, but we'd just wave and keep walking. Study groups would fall apart because coordinating over email was a pain. And honestly? I missed those random conversations that used to happen when we all hung out in the same spots.

So I decided to build something that could bring that back—a digital space where students can actually connect, whether it's coordinating study groups, sharing lecture notes, or just catching up between classes. I wanted it to feel like our campus lounge, not some corporate Slack clone. That's why the UI is clean but vibrant—college life should feel lively, you know?

Think of FadMann as your digital campus lounge. Where conversations flow naturally and you don't have to dig through email chains to share a file.

---

## Features

### What's Working Now

- **User accounts** - Register and log in with secure JWT authentication
- **Public chat rooms** - Join default rooms like General, Study Groups, and Campus Events
- **Real-time messaging** - Messages appear instantly thanks to WebSocket connections (no page refresh needed!)
- **Message history** - All your conversations are saved and load when you join a room
- **Typing indicators** - See when someone's typing a response
- **Clean, vibrant UI** - Built with vanilla JavaScript (no heavy frameworks) so it loads fast

### Coming Soon

I'm working on adding:
- File sharing (because email attachments are the worst)
- Voice messages (sometimes typing isn't enough)
- Message reactions (for those quick responses)
- Push notifications (so you don't miss important messages)

---

## Tech Stack

I kept things simple and focused on learning:

- **Backend:** FastAPI (Python) - Fast, modern, and the docs are actually readable
- **Authentication:** JWT tokens with python-jose - Secure but not overcomplicated
- **Real-time:** Native WebSockets - No need for extra libraries, FastAPI handles it
- **Database:** SQLite with SQLAlchemy - Perfect for development, easy to migrate later
- **Frontend:** Vanilla HTML/CSS/JavaScript - No framework bloat, just clean code
- **Deployment:** Ready for Render (see Deployment section)

I chose these because they're beginner-friendly but still production-ready. Plus, I wanted to understand how everything works under the hood instead of just using magic frameworks.

---

## Screenshots

_Coming soon! I'll add screenshots of the chat interface, room selection, and real-time messaging in action._

<!-- TODO: Add screenshots -->
<!-- - Main chat interface -->
<!-- - Room selection -->
<!-- - Real-time messaging demo -->
<!-- - Mobile responsive view -->

---

## Local Setup

Here's how to get FadMann running on your machine. I've tested this on Windows, but it should work on macOS and Linux too (just adjust the virtual environment activation commands).

### Prerequisites

- Python 3.8 or higher (check with `python --version`)
- pip (comes with Python)

### Step 1: Create Virtual Environment

**PowerShell:**
```powershell
python -m venv venv
```

**CMD:**
```cmd
python -m venv venv
```

### Step 2: Activate Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**CMD:**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` at the start of your prompt when it's activated.

### Step 3: Install Dependencies

**PowerShell/CMD:**
```powershell
pip install -r requirements.txt
```

### Step 4: Start the Server

The backend serves both the API and the frontend static files, so you only need to run one command:

**PowerShell/CMD:**
```powershell
python run.py
```

You should see something like:
```
🚀 Starting FadMann...
📱 Open http://localhost:8000 in your browser
💡 Press Ctrl+C to stop

INFO:     Started server process
INFO:     Waiting for application startup.
✓ Database initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Open in Browser

Navigate to **http://localhost:8000** in your browser. The frontend is automatically served by FastAPI—no separate server needed!

### Step 6: Test WebSocket Connection

To verify real-time messaging is working:

1. Open the app at `http://localhost:8000`
2. Register a new account or log in
3. Join a room (try "General")
4. Open Developer Tools (F12) → Network tab → Filter by "WS"
5. Send a message in the chat
6. You should see a WebSocket connection to `/api/ws/{room_id}` with status "101 Switching Protocols"

**Quick real-time test:**
- Open the app in two browser windows (or one normal + one incognito)
- Log in as different users
- Join the same room in both
- Send a message from one window
- It should appear instantly in the other window!

### Troubleshooting

**Port 8000 already in use?**
- Close whatever's using that port, or change it in `run.py` (line 21, change `port=8000` to something else like `port=8080`)

**Virtual environment won't activate?**
- **PowerShell:** Run the execution policy command from Step 2
- **CMD:** Make sure you're using `activate.bat`, not the `.ps1` file

**Module not found errors?**
- Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
- Try reinstalling: `pip install -r requirements.txt`

**WebSocket not connecting?**
- Check the browser console (F12) for errors
- Make sure the backend is running
- Verify you're logged in (WebSocket requires authentication)

---

## Project Structure

```
fadmann/
├── backend/              # FastAPI backend
│   ├── app.py           # Main FastAPI app (routes, static files, CORS)
│   ├── routes.py        # API endpoints (auth, rooms, messages)
│   ├── models.py        # SQLAlchemy database models
│   ├── database.py      # Database setup and session management
│   ├── websocket.py     # WebSocket connection manager
│   ├── auth.py          # JWT authentication helpers
│   └── validation.py    # Input validation
├── frontend/            # Static frontend files
│   ├── index.html       # Main HTML page
│   ├── css/
│   │   └── style.css    # All the styling
│   └── js/
│       └── app.js       # Frontend logic (WebSocket, API calls)
├── scripts/
│   └── run.ps1         # Quick start script for Windows
├── data/                # SQLite database (auto-created)
├── requirements.txt     # Python dependencies
├── run.py              # Simple runner script
└── README.md           # This file
```

---

## Roadmap

Here's what I'm planning to build next:

### ✅ Phase 1: Foundation (Done!)
- FastAPI backend with WebSocket support
- SQLite database setup
- Basic project structure
- One-command runner script

### ✅ Phase 2: Core Features (Done!)
- User registration and login
- JWT token authentication
- Basic messaging
- WebSocket real-time updates
- Message history

### ✅ Phase 3: UI & Rooms (Done!)
- Public room functionality
- Chat interface
- Message display
- Typing indicators
- Vibrant UI design

### 🚧 Phase 4: File Sharing (In Progress)
- File upload endpoint
- File type validation
- Storage system
- File display in chat
- Download functionality

### 📋 Phase 5: Voice Messages & Reactions
- Audio recording interface
- Voice message upload and playback
- Emoji reaction system
- Real-time reaction updates

### 📋 Phase 6: Polish & Deploy
- Push notifications
- Notification settings
- Error handling improvements
- Mobile responsive design
- Production deployment on Render

I'm learning as I go, so this roadmap might change. If you have suggestions or want to contribute, feel free to reach out!

---

## Development Notes

The app runs in development mode with auto-reload enabled. Any changes to Python files will automatically restart the server, which is super helpful when you're debugging.

### Environment Variables

If you need to customize settings, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Database

The SQLite database is automatically created in the `data/` directory on first run. Default rooms (General, Study Groups, Campus Events) are created automatically too.

### Authentication

FadMann uses JWT tokens for authentication:
- Tokens are signed and secure
- They expire after 7 days
- Stored in browser localStorage
- All protected endpoints require a valid token

See `backend/AUTH_FLOW.md` for more details on how authentication works.

---

## Deployment to Render

I've set this up to deploy easily on Render. Here's how to get it live:

### Prerequisites

- A GitHub account with your code pushed to a repository
- A Render account (free tier works fine)

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub** (if you haven't already)
2. **Go to Render Dashboard** → New → Blueprint
3. **Connect your GitHub repository**
4. **Render will automatically detect `render.yaml`** and configure everything
5. **Set environment variables** in the Render dashboard:
   - `JWT_SECRET_KEY`: Auto-generated by Render (or generate manually with `python scripts/generate_secret.py`)
   - `CORS_ORIGINS`: Your Render app URL (e.g., `https://fadmann.onrender.com`)
6. **Deploy!**

### Option 2: Manual Setup

1. **Push your code to GitHub**
2. **Go to Render Dashboard** → New → Web Service
3. **Connect your repository**
4. **Configure the service:**
   - **Name:** `fadmann` (or whatever you want)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
5. **Set Environment Variables:**
   - `JWT_SECRET_KEY`: Generate a strong random key:
     ```bash
     python scripts/generate_secret.py
     ```
     Or use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `JWT_ALGORITHM`: `HS256` (optional, this is the default)
   - `JWT_EXPIRE_DAYS`: `7` (optional, this is the default)
   - `CORS_ORIGINS`: Your Render app URL (e.g., `https://fadmann.onrender.com`)
   - `DATABASE_PATH`: `/opt/render/project/src/data` (optional, for persistent storage)
6. **Click "Create Web Service"**

### Important Notes

**SQLite on Render:**
- SQLite works on Render, but the filesystem is **ephemeral** - your database will be wiped on every redeploy
- For production with persistent data, consider upgrading to Render's PostgreSQL database
- For now, SQLite is fine for testing and demos

**CORS Configuration:**
- The app automatically uses the `CORS_ORIGINS` environment variable
- Set it to your Render domain (e.g., `https://fadmann.onrender.com`)
- You can add multiple origins separated by commas: `https://app1.onrender.com,https://app2.onrender.com`

**Health Check:**
- Render will automatically check `/health` endpoint to ensure your app is running
- This endpoint is already configured in the app

### After Deployment

Once deployed, your app will be available at `https://your-app-name.onrender.com`. The first deploy might take a few minutes, but subsequent deploys are faster.

**Free Tier Limitations:**
- Render's free tier spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- Perfect for demos and testing, but consider upgrading for production use

### Troubleshooting

**Build fails:**
- Check that all dependencies are in `requirements.txt`
- Verify Python version (Render uses Python 3.11 by default)

**App crashes on startup:**
- Check logs in Render dashboard
- Verify all environment variables are set
- Make sure `JWT_SECRET_KEY` is set (it's required)

**Database issues:**
- Remember that SQLite data is ephemeral on Render
- Consider using Render PostgreSQL for persistent data

---

## License

MIT License - feel free to use this for your own projects or learn from it!

---

**Built with ❤️ by Emmanuel Akwasi Opoku (@emmanuelakwasi) - CS Student @ Grambling State University**

Happy chatting! 🎓💬
