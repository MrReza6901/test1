from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATA_FILE = Path("data.json")

def load_data():
    if not DATA_FILE.exists():
        return {"users": [], "checkins": {}}
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")
        fullname = request.form.get("fullname")

        if action == "register":
            for u in data["users"]:
                if u["username"] == username:
                    return "نام کاربری تکراری است", 400
            data["users"].append({"username": username, "password": password, "fullname": fullname})
            save_data(data)
            session["user"] = username
            return redirect(url_for("dashboard"))

        elif action == "login":
            for u in data["users"]:
                if u["username"] == username and u["password"] == password:
                    session["user"] = username
                    return redirect(url_for("dashboard"))
            return "اطلاعات ورود اشتباه است", 400

    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    data = load_data()
    user = session["user"]
    today = datetime.today().strftime('%Y-%m-%d')
    checkins = data["checkins"].get(today, [])

    is_admin = user == "admin"
    user_data = next((u for u in data["users"] if u["username"] == user), None)
    all_users = sorted(data["users"], key=lambda x: x["fullname"])

    return render_template("admin.html" if is_admin else "index.html",
                           user=user_data,
                           checkins=checkins,
                           all_users=all_users,
                           today=today,
                           is_admin=is_admin)

@app.route("/checkin", methods=["POST"])
def checkin():
    if "user" not in session:
        return redirect(url_for("index"))

    data = load_data()
    user = session["user"]
    today = datetime.today().strftime('%Y-%m-%d')

    if today not in data["checkins"]:
        data["checkins"][today] = []

    if user not in data["checkins"][today]:
        data["checkins"][today].append(user)
        save_data(data)

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
