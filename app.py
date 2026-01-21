from flask import Flask, render_template, request, redirect, send_file, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from openpyxl import Workbook
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "super-secret-key-123"  # change later

# -------------------- DATABASE CONFIG --------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db():
    return psycopg2.connect(DATABASE_URL)

# -------------------- ADMIN CONFIG --------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hashirxyzz1z"

# -------------------- INIT DATABASE --------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS children (
            id SERIAL PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            disease TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- ADMIN DECORATOR --------------------
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin-login")
        return func(*args, **kwargs)
    return wrapper

# -------------------- ADMIN LOGIN --------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME and
            request.form.get("password") == ADMIN_PASSWORD
        ):
            session["admin"] = True
            return redirect("/view")
        return "<script>alert('❌ Invalid credentials');window.location='/admin-login'</script>"

    return render_template("admin_login.html")

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin-login")

# -------------------- HOME --------------------
@app.route("/")
def index():
    return render_template("form.html")

# -------------------- ADD DATA --------------------
# -------------------- ADD DATA --------------------
@app.route("/add", methods=["POST"])
def add_child():
    # Get form values
    name = request.form.get("name")
    age = request.form.get("age")
    gender = request.form.get("gender")
    
    # Convert empty height/weight to None (NULL in DB)
    height = request.form.get("height")
    height = float(height) if height.strip() != "" else None

    weight = request.form.get("weight")
    weight = float(weight) if weight.strip() != "" else None

    disease = request.form.get("disease") or None

    # Prepare data tuple
    data = (name, age, gender, height, weight, disease)

    # Insert into database
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO children (name, age, gender, height, weight, disease)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, data)

    child_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return redirect(f"/result/{child_id}")

# -------------------- VIEW (ADMIN) --------------------
@app.route("/view")
@admin_required
def view_children():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM children ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()

    rows = ""
    for c in data:
        rows += f"""
        <tr>
            <td>{c[0]}</td>
            <td>{c[1]}</td>
            <td>{c[2]}</td>
            <td>{c[3]}</td>
            <td>{c[4] if c[4] else '-'}</td>
            <td>{c[5] if c[5] else '-'}</td>
            <td>{c[6] if c[6] else '-'}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Children Healthcare Database</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="p-4">
        <div class="container">
            <h1 class="mb-4">Children Healthcare Database</h1>
            <p>Total Records: <strong>{len(data)}</strong></p>
            <table class="table table-striped table-bordered table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th><th>Name</th><th>Age</th><th>Gender</th>
                        <th>Height</th><th>Weight</th><th>Disease</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <a href="/download" class="btn btn-success me-2">⬇ Download Excel</a>
            <a href="/delete_all" class="btn btn-danger me-2">🗑 Delete All</a>
            <a href="/logout" class="btn btn-secondary">🚪 Logout</a>
        </div>
    </body>
    </html>
    """

# -------------------- DELETE ALL --------------------
@app.route("/delete_all")
@admin_required
def delete_all():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM children")
    conn.commit()
    conn.close()
    return redirect("/view")

# -------------------- RESULT PAGE --------------------
@app.route("/result/<int:child_id>")
def result(child_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM children WHERE id = %s", (child_id,))
    child = cur.fetchone()
    conn.close()

    if not child:
        return "❌ Child not found"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registration Result</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="p-4">
        <div class="container text-center">
            <div class="card mx-auto" style="max-width: 500px;">
                <div class="card-header bg-success text-white">
                    <h3>Registration Successful ✅</h3>
                </div>
                <div class="card-body text-start">
                    <p><strong>ID:</strong> {child[0]}</p>
                    <p><strong>Name:</strong> {child[1]}</p>
                    <p><strong>Age:</strong> {child[2]}</p>
                    <p><strong>Gender:</strong> {child[3]}</p>
                    <p><strong>Height:</strong> {child[4] if child[4] else '-'}</p>
                    <p><strong>Weight:</strong> {child[5] if child[5] else '-'}</p>
                    <p><strong>Disease:</strong> {child[6] if child[6] else '-'}</p>
                </div>
                <div class="card-footer text-center">
                    <a href="/" class="btn btn-primary">Add Another</a>
                    <a href="/view" class="btn btn-secondary">View All</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# -------------------- DOWNLOAD EXCEL --------------------
@app.route("/download")
@admin_required
def download_excel():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM children")
    data = cur.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "Name", "Age", "Gender", "Height", "Weight", "Disease"])

    for row in data:
        ws.append(row)

    filename = f"children_healthcare_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)

    return send_file(filename, as_attachment=True)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


