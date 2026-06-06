# Real Chat Room

Real Chat Room is a Flask web app for live group and private messaging. It uses Flask-SocketIO for real-time chat, supports custom team rooms, friend-code based private messages, online user lists, typing indicators, and an optional ngrok public URL when the app starts.

## Features

- Join with a username and status
- Chat in the default `General` room
- Create or join rooms with a team code
- Send private messages to online users
- Quick connect by team code or friend code
- Live online user list
- Typing indicators
- Responsive Bootstrap interface

## Tech Stack

- Python
- Flask
- Flask-SocketIO
- Bootstrap 5
- Socket.IO client
- pyngrok

## Project Structure

```text
chat-app/
├── app.py
├── requirements.txt
├── static/
│   └── css/
│       └── styles.css
└── templates/
    ├── index.html
    └── chat.html
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If `requirements.txt` installation fails because of the extra install text, install the packages directly:

```powershell
pip install Flask Flask-SocketIO eventlet pyngrok
```

## Run The App

```powershell
python app.py
```

Open the local app in your browser:

```text
http://localhost:5000
```

When ngrok is configured, the terminal may also print a public URL that can be shared with others.

## How To Use

1. Enter your username and optional status.
2. Choose `General` or enter a team code to create/join a room.
3. Enter a friend's username/code to start a private chat when they are online.
4. Use the chat page sidebar to switch rooms or select online users.

## Notes

- Messages and rooms are stored in memory, so they reset when the server restarts.
- Change `SECRET_KEY` in `app.py` before using this in production.
- Do not commit virtual environments, cache files, or local secrets.
