from flask import Flask, render_template, request, redirect, session, url_for
import json
from datetime import date
import os

app = Flask(__name__)
app.secret_key = 'verysecret'

DATA_FOLDER = 'data'
MEMBERS_FILE = os.path.join(DATA_FOLDER, 'members.json')
CHECKINS_FILE = os.path.join(DATA_FOLDER, 'checkins.json')

def load_members():
    with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_checkins(checkins):
    with open(CHECKINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkins, f, ensure_ascii=False, indent=2)

def load_checkins():
    if not os.path.exists(CHECKINS_FILE):
        return {}
    with open(CHECKINS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect('/dashboard')
        return render_template('login.html', error='نام کاربری یا رمز اشتباه است')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'admin' not in session:
        return redirect('/')
    members = load_members()
    today = str(date.today())
    checkins = load_checkins()

    if request.method == 'POST':
        checked = request.form.getlist('checked')
        checkins[today] = checked
        save_checkins(checkins)

    today_checked = checkins.get(today, [])
    return render_template('dashboard.html', members=members, checked=today_checked, today=today)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/add-member', methods=['POST'])
def add_member():
    if 'admin' not in session:
        return redirect('/')
    members = load_members()
    new_member = request.form['fullname'].strip()
    if new_member:
        members.append(new_member)
        with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted(set(members)), f, ensure_ascii=False, indent=2)
    return redirect('/dashboard')

@app.route('/report')
def report():
    if 'admin' not in session:
        return redirect('/')
    members = load_members()
    today = str(date.today())
    checkins = load_checkins()
    checked = checkins.get(today, [])
    return {
        "date": today,
        "checked": checked,
        "unchecked": [m for m in members if m not in checked]
    }

if __name__ == '__main__':
    app.run(debug=True)
