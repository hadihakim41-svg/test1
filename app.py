from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = "yoursecretkey"

DATABASE = "employees.db"

# Connect to database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize DB
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            employee_id TEXT,
            machine TEXT,
            department TEXT,
            datetime TEXT
        )
    """)
    conn.commit()
    conn.close()

def ensure_column_exists(column_name, column_type):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(employees)")
    columns = [info[1] for info in c.fetchall()]
    if column_name not in columns:
        c.execute(f"ALTER TABLE employees ADD COLUMN {column_name} {column_type}")
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Home page
@app.route('/')
def home():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Simple login roles
    if username == "admin" and password == "admin123":
        session['username'] = username
        session['role'] = 'admin'
        return redirect(url_for('dashboard'))
    elif username == "user" and password == "user123":
        session['username'] = username
        session['role'] = 'user'
        return redirect(url_for('dashboard'))
    else:
        return "Invalid username or password"

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees")
    records = cursor.fetchall()

    # Assign custom numbering (No = 1, 2, 3, …)
    numbered_records = []
    for i, row in enumerate(records, start=1):
        numbered_records.append((i, *row[1:]))

    return render_template('dashboard.html', records=numbered_records, username=session['username'], role=session['role'])

# Add record
@app.route('/add', methods=['POST'])
def add_record():
    if 'username' not in session:
        return redirect(url_for('home'))

    name = request.form['name']
    employee_id = request.form['employee_id']
    machine = request.form['machine']
    department = request.form.get('department', '')

    # Malaysia time
    malaysia_tz = timezone(timedelta(hours=8))
    dt = datetime.now(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO employees (name, employee_id, machine, department, datetime) VALUES (?, ?, ?, ?, ?)",
                   (name, employee_id, machine, department, dt))
    db.commit()
    return redirect(url_for('dashboard'))

# Delete record (admin only)
@app.route('/delete_all')
def delete_all_records():
    if 'username' not in session or session.get('role') != 'admin':
        return "Access Denied: Admins only"

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees")
    db.commit()
    # Reset auto-increment counter to 1
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='employees'")
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:no>')
def delete_record(no):
    if 'username' not in session or session.get('role') != 'admin':
        return "Access Denied: Admins only"
    db = get_db()
    cursor = db.cursor()
    # Find actual ID based on order
    cursor.execute("SELECT id FROM employees ORDER BY id")
    ids = [row[0] for row in cursor.fetchall()]
    if 0 < no <= len(ids):
        actual_id = ids[no - 1]
        cursor.execute("DELETE FROM employees WHERE id=?", (actual_id,))
        db.commit()
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    ensure_column_exists("department", "TEXT")
    app.run(debug=True)