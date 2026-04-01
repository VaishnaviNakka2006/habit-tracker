from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)

def get_db():
    return sqlite3.connect("habits.db")

# create table
with get_db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS habits(
        id INTEGER PRIMARY KEY,
        name TEXT,
        streak INTEGER,
        last_done TEXT
    )
    """)

@app.route("/")
def index():
    conn = get_db()
    habits = conn.execute("SELECT * FROM habits").fetchall()
    conn.close()
    return render_template("index.html", habits=habits)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    conn = get_db()
    conn.execute(
        "INSERT INTO habits (name, streak, last_done) VALUES (?,0,'')",
        (name,)
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/done/<int:id>")
def done(id):
    conn = get_db()
    habit = conn.execute(
        "SELECT streak, last_done FROM habits WHERE id=?",
        (id,)
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
    conn.execute("DELETE FROM habits WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()

    if request.method == "POST":
        new_name = request.form["name"]
        conn.execute(
            "UPDATE habits SET name=? WHERE id=?",
            (new_name, id)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    habit = conn.execute(
        "SELECT * FROM habits WHERE id=?",
        (id,)
    ).fetchone()
    conn.close()

    return render_template("edit.html", habit=habit)

if __name__ == "__main__":
    app.run(debug=True)