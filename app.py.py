from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # change this for security

# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        employee_id TEXT,
        machine TEXT,
        datetime TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )''')
    conn.commit()
    conn.close()

# Home Page (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            session['role'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid login")
    return render_template('login.html')

# Dashboard (different view by role)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    records = c.fetchall()
    conn.close()

    role = session['role']
    if role == "admin":
        return render_template('admin.html', records=records)
    elif role == "user":
        return render_template('dashboard.html', records=records)
    else:
        return render_template('public.html', records=records)

# Add new entry (user)
@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session or session['role'] == 'public':
        return redirect(url_for('login'))

    name = request.form['name']
    emp_id = request.form['employee_id']
    machine = request.form['machine']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO employees (name, employee_id, machine, datetime) VALUES (?, ?, ?, ?)",
              (name, emp_id, machine, now))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# Admin delete/edit
@app.route('/delete/<int:id>')
def delete(id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM employees WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)