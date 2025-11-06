from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime, timedelta, timezone
import os

app = Flask(__name__)
app.secret_key = "yoursecretkey"

DATABASE = "employees.db"

# Connect to DB
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Create or alter table
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

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == "admin" and password == "admin123":
        session['username'] = username
        return redirect(url_for('dashboard'))
    elif username == "user" and password == "user123":
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return "Invalid username or password"

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees")
    records = cursor.fetchall()
    return render_template('dashboard.html', records=records, username=session['username'])

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

@app.route('/delete/<int:id>')
def delete_record(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id=?", (id,))
    db.commit()

    # Reset ID to start from 1 again if table empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='employees'")
        db.commit()

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    ensure_column_exists("department", "TEXT")
    app.run(debug=True)