from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("habits.db")

# ---------------- DATABASE ----------------

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
    try:
        if "user_id" not in session:
            return render_template("login.html")

        conn = get_db()
        habits = conn.execute(
            "SELECT * FROM habits WHERE user_id=?",
            (session["user_id"],)
        ).fetchall()
        conn.close()

        return render_template("index.html", habits=habits)

    except Exception as e:
        return str(e) + "<br><pre>" + traceback.format_exc() + "</pre>"

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
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()

    habit = conn.execute(
        "SELECT streak, last_done FROM habits WHERE id=? AND user_id=?",
        (id, session["user_id"])
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
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    conn.execute(
        "DELETE FROM habits WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()

    if request.method == "POST":
        new_name = request.form["name"]
        conn.execute(
            "UPDATE habits SET name=? WHERE id=? AND user_id=?",
            (new_name, id, session["user_id"])
        )
        conn.commit()
        conn.close()
        return redirect("/")

    habit = conn.execute(
        "SELECT * FROM habits WHERE id=? AND user_id=?",
        (id, session["user_id"])
    ).fetchone()
    conn.close()

    return render_template("edit.html", habit=habit)

if __name__ == "__main__":
    app.run(debug=True)