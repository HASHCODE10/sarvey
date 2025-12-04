from flask import Flask, render_template, request, redirect, send_file, session

import sqlite3
import os
from openpyxl import Workbook
import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key-123"   # Change this!

DB_NAME = "healthcare.db"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hashirxyzz1z"  # Your admin password


# -------------------- Create database & table --------------------
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        with open("healthcare.sql", "r") as f:
            conn.executescript(f.read())
        conn.close()
        print("✅ Database created successfully.")

init_db()


# -------------------- ADMIN LOGIN CHECK --------------------
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin-login")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# -------------------- ADMIN LOGIN PAGE --------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/view")
        else:
            return """
            <script>
            alert('❌ Invalid username or password!');
            window.location='/admin-login';
            </script>
            """

    return """
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body {
                background: #111;
                font-family: Arial;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .box {
                background: #1e1e1e;
                padding: 30px;
                border-radius: 10px;
                width: 350px;
            }
            input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: none;
                border-radius: 5px;
            }
            button {
                width: 100%;
                padding: 10px;
                background: #4facfe;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h2 style="text-align:center;color:#00f2fe;">Admin Login</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Admin Username" required>
                <input type="password" name="password" placeholder="Admin Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """


# -------------------- ADMIN LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin-login")


# -------------------- Home route --------------------
@app.route("/")
def index():
    return render_template("form.html")


# -------------------- Add data route --------------------
@app.route("/add", methods=["POST"])
def add_child():
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    height = request.form["height"]
    weight = request.form["weight"]
    disease = request.form["disease"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO children (name, age, gender, height, weight, disease)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, age, gender, height, weight, disease))

    child_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return redirect(f"/result/{child_id}")


# -------------------- View Route (ADMIN ONLY) --------------------
@app.route("/view")
@admin_required
def view_children():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children")
    data = cursor.fetchall()
    conn.close()

    rows = ""
    for child in data:
        rows += f"""
        <tr>
            <td>{child[0]}</td>
            <td>{child[1]}</td>
            <td>{child[2]}</td>
            <td>{child[3]}</td>
            <td>{child[4]}</td>
            <td>{child[5]}</td>
            <td>{child[6]}</td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Children Healthcare Records</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            padding: 20px;
        }}

        h1 {{
            color: #00f2fe;
            text-align: center;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: #1e1e1e;
        }}

        th, td {{
            border: 1px solid #444;
            padding: 10px;
            text-align: center;
        }}

        th {{
            background: #4facfe;
            color: black;
        }}

        tr:nth-child(even) {{
            background: #222;
        }}

        .count {{
            text-align: center;
            font-size: 20px;
            margin-top: 10px;
        }}

        .logout {{
            text-align:center;
            margin-top:20px;
        }}

        a {{
            color:#4facfe;
        }}
    </style>
</head>
<body>

<h1>👶 Children Healthcare Database</h1>

<div class="count">Total Records: {len(data)}</div>

<table>
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Age</th>
        <th>Gender</th>
        <th>Height (cm)</th>
        <th>Weight (kg)</th>
        <th>Disease</th>
    </tr>
    {rows}
</table>

<div class="logout">
    <a href="/delete_all">🗑 Delete All</a> | 
    <a href="/logout">🚪 Logout</a>
</div>

</body>
</html>
"""


# -------------------- Delete All (ADMIN ONLY) --------------------
@app.route("/delete_all")
@admin_required
def delete_all():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM children")
    conn.commit()
    conn.close()

    return """
    <script>
    alert('✅ All records deleted successfully!');
    window.location='/view';
    </script>
    """


# -------------------- RESULT PAGE --------------------
@app.route("/result/<int:child_id>")
def result(child_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
    child = cursor.fetchone()

    conn.close()

    if child is None:
        return "❌ Child not found!"

    return f"""
    <html>
    <head>
        <title>Registration Result</title>
        <style>
            body {{
                background: #111;
                color: white;
                font-family: Arial;
                padding: 40px;
            }}
            .card {{
                background: #1e1e1e;
                padding: 30px;
                border-radius: 10px;
                max-width: 500px;
                margin: auto;
            }}
            h2 {{
                color: #00f2fe;
                text-align: center;
            }}
            p {{
                font-size: 18px;
                line-height: 1.5;
            }}
            a {{
                color: #4facfe;
                text-decoration: none;
                display: block;
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>

    <div class="card">
        <h2>✅ Registration Successful</h2>
        <p><b>ID :</b> {child[0]}</p>
        <p><b>Name :</b> {child[1]}</p>
        <p><b>Age :</b> {child[2]}</p>
        <p><b>Gender :</b> {child[3]}</p>
        <p><b>Height :</b> {child[4]} cm</p>
        <p><b>Weight :</b> {child[5]} kg</p>
        <p><b>Disease :</b> {child[6]}</p>

        <a href="/">➕ Register Another</a>
        <a href="/admin-login">🔑 Admin Login</a>
    </div>

    </body>
    </html>
    """
@app.route("/download")
@admin_required
def download_excel():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM children")
    data = cursor.fetchall()
    conn.close()

    # Create Excel file
    wb = Workbook()
    ws = wb.active
    ws.title = "Children Healthcare Data"

    # Header row
    headers = ["ID", "Name", "Age", "Gender", "Height", "Weight", "Disease"]
    ws.append(headers)

    # Add data rows
    for row in data:
        ws.append(row)

    # Filename with date
    filename = f"children_healthcare_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = f"./{filename}"

    # Save file
    wb.save(filepath)

    # Send file to user
    return send_file(filepath, as_attachment=True)

# -------------------- Run server --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
