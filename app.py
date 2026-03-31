from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, timedelta
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ Better DB path (important for deployment)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "habits.db")

def get_db():
    return sqlite3.connect(DB_PATH)

# ---------------- CREATE TABLES ----------------

with get_db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS habits(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        name TEXT,
        streak INTEGER,
        last_done TEXT
    )
    """)

# ---------------- AUTH ----------------

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?,?)",
        (username, password)
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]

    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

# ---------------- MAIN ----------------

@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("login.html")  # make sure this file exists

    conn = get_db()
    habits = conn.execute(
        "SELECT * FROM habits WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("index.html", habits=habits)

# ---------------- HABITS ----------------

@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/")

    name = request.form["name"]

    conn = get_db()
    conn.execute(
        "INSERT INTO habits (user_id, name, streak, last_done) VALUES (?, ?, 0, '')",
        (session["user_id"], name)
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/done/<int:id>")
def done(id):
    conn = get_db()

    habit = conn.execute(
        "SELECT streak, last_done FROM habits WHERE id=? AND user_id=?",
        (id, session.get("user_id"))
    ).fetchone()

    if not habit:
        return redirect("/")

    today = date.today()
    today_str = str(today)

    last_done = habit[1]

    if last_done:
        last_date = date.fromisoformat(last_done)
    else:
        last_date = None

    if last_date == today:
        return redirect("/")

    elif last_date == today - timedelta(days=1):
        streak = habit[0] + 1
    else:
        streak = 1

    conn.execute(
        "UPDATE habits SET streak=?, last_done=? WHERE id=?",
        (streak, today_str, id)
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute(
        "DELETE FROM habits WHERE id=? AND user_id=?",
        (id, session.get("user_id"))
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()

    if request.method == "POST":
        new_name = request.form["name"]
        conn.execute(
            "UPDATE habits SET name=? WHERE id=? AND user_id=?",
            (new_name, id, session.get("user_id"))
        )
        conn.commit()
        conn.close()
        return redirect("/")

    habit = conn.execute(
        "SELECT * FROM habits WHERE id=? AND user_id=?",
        (id, session.get("user_id"))
    ).fetchone()
    conn.close()

    return str(habits)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)