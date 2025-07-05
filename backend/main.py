from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import date

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
conn = sqlite3.connect("checkin.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    fullname TEXT,
    password TEXT
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT
)
""")
conn.commit()

# Models
class UserRegister(BaseModel):
    username: str
    fullname: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class CheckinRequest(BaseModel):
    username: str

# API
@app.get("/")
def root():
    return {"status": "Prayer Check-in API running."}

@app.post("/register")
def register(user: UserRegister):
    try:
        c.execute("INSERT INTO users (username, fullname, password) VALUES (?, ?, ?)",
                  (user.username, user.fullname, user.password))
        conn.commit()
        return {"message": "User registered."}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")

@app.post("/login")
def login(user: UserLogin):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (user.username, user.password))
    if c.fetchone():
        return {"message": "Login successful."}
    raise HTTPException(status_code=401, detail="Invalid credentials.")

@app.post("/checkin")
def checkin(data: CheckinRequest):
    c.execute("SELECT id FROM users WHERE username = ?", (data.username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found.")

    user_id = row[0]
    today = str(date.today())
    c.execute("SELECT * FROM checkins WHERE user_id = ? AND date = ?", (user_id, today))
    if c.fetchone():
        return {"message": "Already checked in today."}

    c.execute("INSERT INTO checkins (user_id, date) VALUES (?, ?)", (user_id, today))
    conn.commit()
    return {"message": "Check-in successful."}

@app.get("/checkins/today")
def get_today_checkins():
    today = str(date.today())
    c.execute("SELECT u.fullname, u.username, (SELECT 1 FROM checkins WHERE user_id = u.id AND date = ?) IS NOT NULL AS checked FROM users u ORDER BY u.fullname", (today,))
    users = c.fetchall()
    return [{"name": u[0], "status": "🌸" if u[2] else "🥺"} for u in users]

@app.get("/admin/report", response_class=HTMLResponse)
def report():
    today = str(date.today())
    c.execute("SELECT fullname, (SELECT 1 FROM checkins WHERE user_id = u.id AND date = ?) IS NOT NULL AS checked FROM users u ORDER BY fullname", (today,))
    users = c.fetchall()
    report_html = f"""
    <html><head><meta charset='utf-8'><style>
    body {{ font-family: sans-serif; direction: rtl; }}
    .user {{ margin: 6px 0; }}
    </style></head><body>
    <h3>📖برنامه عهد جمعی</h3>
    <p>⌚یوم: {today.replace('-', '/')}</p>
    <div>
    """
    for i, user in enumerate(users, 1):
        symbol = "🌸" if user[1] else "🥺"
        report_html += f"<div class='user'>{i}. {user[0]} {symbol}</div>"
    report_html += "</div></body></html>"
    return report_html
