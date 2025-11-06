import sys
import sqlite3

# ensure stdout uses UTF-8 so emoji prints on Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    # reconfigure may not be available in some environments — fallback silently
    pass

# Connect to the same database as your Flask app
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Create the table if it doesn’t exist (for safety)
c.execute('''CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)''')

# Insert user roles
users = [
    ("admin", "admin123", "admin"),   # full access
    ("user", "user123", "user"),      # limited access
    ("guest", "guest123", "public")   # view only
]

for u in users:
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", u)
    except sqlite3.IntegrityError:
        print(f"User {u[0]} already exists, skipping...")

conn.commit()
conn.close()

print("✅ User roles setup complete!")