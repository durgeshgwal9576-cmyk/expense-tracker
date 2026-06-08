from flask import Flask, render_template, request, redirect, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = "secret-key"

# ---------------- LOGIN MANAGER SETUP (FIXED 401 ERROR) ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Batata hai ki unauthorized users ko kahan bhejna hai

users = {"admin": {"password": "1234"}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ---------------- DATABASE CONFIG (RENDER COMPATIBLE) ----------------
# Render ke temporary persistent block me db file rakhne ke liye path fix kiya hai
DB_PATH = os.path.join("/tmp", "expenses.db") if os.environ.get("RENDER") else "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES: LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect("/")
        return "Invalid credentials"

    return render_template("login.html")

# ---------------- ROUTES: LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------------- ROUTES: HOME ----------------
@app.route("/")
@login_required
def home():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses")
    rows = cur.fetchall()
    conn.close()

    expenses = [
        {
            "id": r[0],
            "date": r[1],
            "category": r[2],
            "description": r[3],
            "amount": r[4]
        )
        for r in rows
    ]

    total = sum(e["amount"] for e in expenses)

    return render_template("index.html", expenses=expenses, total=total)

# ---------------- ROUTES: ADD ----------------
@app.route("/add", methods=["POST"])
@login_required
def add():
    date = request.form["date"]
    category = request.form["category"]
    description = request.form["description"]
    amount = float(request.form["amount"])

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO expenses (date, category, description, amount)
        VALUES (?, ?, ?, ?)
    """, (date, category, description, amount))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- ROUTES: DELETE ----------------
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- ROUTES: EXCEL DOWNLOAD ----------------
@app.route("/download/excel")
@login_required
def excel():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    file_path = os.path.join("/tmp", "expenses.xlsx") if os.environ.get("RENDER") else "expenses.xlsx"
    df.to_excel(file_path, index=False)
    conn.close()
    return send_file(file_path, as_attachment=True)

# ---------------- ROUTES: PDF DOWNLOAD ----------------
@app.route("/download/pdf")
@login_required
def pdf():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses")
    data = cur.fetchall()
    conn.close()

    file_path = os.path.join("/tmp", "expenses.pdf") if os.environ.get("RENDER") else "expenses.pdf"
    c = canvas.Canvas(file_path)

    y = 800
    c.drawString(100, y + 20, "Expense Report")
    c.drawString(100, y + 10, "--------------------------------------------")
    for r in data:
        if y < 50:  # Agar page khatam hone lage toh safe side padding
            c.showPage()
            y = 800
        c.drawString(100, y, f"{r[1]} | {r[2]} | {r[3]} | Rs.{r[4]}")
        y -= 20

    c.save()
    return send_file(file_path, as_attachment=True)

# ---------------- RUN (PRODUCTION & LOCAL COMPATIBLE) ----------------
if __name__ == "__main__":
    # Render ya local network ke liye host setup open kiya hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)