from datetime import datetime

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
from pyngrok import ngrok

app = Flask(__name__)
app.config["SECRET_KEY"] = "change_this_to_a_random_secret"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", manage_session=True)

users = {}
sid_to_user = {}
rooms = {"General": []}


def normalize_code(value):
    return "-".join(value.strip().split())


def find_user_by_code(code):
    normalized = normalize_code(code).lower()

    for username, user_data in users.items():
        if username.lower() == normalized or user_data.get("friend_code", "").lower() == normalized:
            return username

    return None


# ---------------- ROUTES ---------------- #
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        status = request.form.get("status", "").strip() or "Available"
        room = request.form.get("room", "").strip() or "General"
        team_code = normalize_code(request.form.get("team_code", ""))
        friend_code = normalize_code(request.form.get("friend_code", ""))

        if not username:
            return render_template("index.html", error="Username is required.", rooms=list(rooms.keys()))

        if team_code:
            room = team_code

        session["username"] = username
        session["status"] = status
        session["room"] = room
        session["friend_code"] = normalize_code(username)
        session["friend_target"] = friend_code

        if room not in rooms:
            rooms[room] = []

        return redirect(url_for("chat"))

    return render_template("index.html", rooms=list(rooms.keys()))


@app.route("/chat")
def chat():
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    return render_template(
        "chat.html",
        username=username,
        status=session.get("status", "Available"),
        room=session.get("room", "General"),
        friend_code=session.get("friend_code", username),
        friend_target=session.get("friend_target", ""),
        rooms=list(rooms.keys()),
    )


# ---------------- SOCKET EVENTS ---------------- #
@socketio.on("connect")
def on_connect():
    username = session.get("username")
    if not username:
        return False

    sid = request.sid
    room = session.get("room", "General")

    users[username] = {
        "sid": sid,
        "status": session.get("status", "Available"),
        "room": room,
        "friend_code": session.get("friend_code", username),
    }

    sid_to_user[sid] = username

    if room not in rooms:
        rooms[room] = []

    if username not in rooms[room]:
        rooms[room].append(username)

    join_room(room)

    emit("user_list", {"users": list(users.keys())}, broadcast=True)

    emit("message", {
        "type": "system",
        "message": f"{username} connected",
        "time": datetime.now().strftime("%H:%M:%S"),
    }, to=room)


@socketio.on("join_room")
def on_join_room(data):
    username = session.get("username")
    new_room = normalize_code(data.get("room", "General")) or "General"

    old_room = users.get(username, {}).get("room", "General")

    if old_room != new_room:
        leave_room(old_room)

        if old_room in rooms and username in rooms[old_room]:
            rooms[old_room].remove(username)

    if new_room not in rooms:
        rooms[new_room] = []

    if username not in rooms[new_room]:
        rooms[new_room].append(username)

    users[username]["room"] = new_room
    join_room(new_room)

    emit("message", {
        "type": "system",
        "message": f"{username} joined {new_room}",
        "time": datetime.now().strftime("%H:%M:%S"),
    }, to=new_room)

    emit("room_changed", {"room": new_room}, to=request.sid)
    emit("user_list", {"users": list(users.keys())}, broadcast=True)


@socketio.on("group_message")
def handle_group_message(data):
    username = session.get("username")
    room = normalize_code(data.get("room", "General")) or "General"
    message = data.get("message", "").strip()

    if not message:
        return

    emit("message", {
        "type": "chat",
        "scope": "group",
        "username": username,
        "status": users[username]["status"],
        "message": message,
        "time": datetime.now().strftime("%H:%M:%S"),
    }, to=room)


@socketio.on("private_message")
def handle_private_message(data):
    sender = session.get("username")
    recipient = find_user_by_code(data.get("to", ""))
    message = data.get("message", "").strip()

    if not message:
        return

    if not recipient:
        emit("private_error", {"message": "Friend code is not online"}, to=request.sid)
        return

    payload = {
        "from": sender,
        "message": message,
        "time": datetime.now().strftime("%H:%M:%S"),
    }

    emit("private_message", payload, to=users[recipient]["sid"])
    emit("private_message", payload, to=request.sid)


@socketio.on("typing")
def typing(data):
    username = session.get("username")

    if data.get("scope") == "private":
        target = find_user_by_code(data.get("target", ""))
        if target in users:
            emit("typing", {"username": username}, to=users[target]["sid"], include_self=False)
    else:
        room = normalize_code(data.get("room", "General")) or "General"
        emit("typing", {"username": username}, to=room, include_self=False)


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    username = sid_to_user.pop(sid, None)

    if not username:
        return

    user_data = users.pop(username, None)

    if user_data:
        room = user_data.get("room", "General")

        if room in rooms and username in rooms[room]:
            rooms[room].remove(username)

        emit("message", {
            "type": "system",
            "message": f"{username} disconnected",
            "time": datetime.now().strftime("%H:%M:%S"),
        }, to=room)

    emit("user_list", {"users": list(users.keys())}, broadcast=True)


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    try:
        ngrok.kill()

        public_url = ngrok.connect(5000)
        print("\nPublic URL:", public_url)

    except Exception as e:
        print("ngrok error:", e)

    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
