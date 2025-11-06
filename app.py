from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'employees.db'


# ---------- DATABASE SETUP ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            employee_id TEXT NOT NULL,
                            machine TEXT NOT NULL,
                            department TEXT,
                            datetime TEXT NOT NULL
                        )''')
        db.commit()


# ---------- AUTO ADD MISSING COLUMN ----------
def add_missing_columns():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(employees)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'department' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN department TEXT")
            db.commit()
            print("✅ Added missing column: department")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# ---------- USER LOGIN ----------
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
    'public': {'password': 'public123', 'role': 'public'}
}


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['role'] = users[username]['role']
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Invalid username or password')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees")
    records = cursor.fetchall()

    return render_template('dashboard.html', records=records, role=session['role'])


# ---------- ADD RECORD ----------
@app.route('/add', methods=['POST'])
def add_record():
    if 'username' not in session:
        return redirect(url_for('home'))

    name = request.form['name']
    employee_id = request.form['employee_id']
    machine = request.form['machine']
    department = request.form.get('department', '')

    # Malaysia time (UTC+8)
    malaysia_tz = timezone(timedelta(hours=8))
    dt = datetime.now(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO employees (name, employee_id, machine, department, datetime) VALUES (?, ?, ?, ?, ?)",
                   (name, employee_id, machine, department, dt))
    db.commit()

    return redirect(url_for('dashboard'))


# ---------- DELETE RECORD ----------
@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('dashboard'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (record_id,))
    db.commit()

    return redirect(url_for('dashboard'))
# ---------- MAIN ----------
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        add_missing_columns()
    app.run(debug=True)