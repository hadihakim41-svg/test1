import sqlite3

conn = sqlite3.connect("employees.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)''')

users = [
    ("admin", "admin123", "admin"),
    ("user", "user123", "user"),
    ("guest", "guest123", "public")
]

for u in users:
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", u)
    except sqlite3.IntegrityError:
        print(f"User {u[0]} already exists, skipping...")

conn.commit()
conn.close()
print("✅ Default users created successfully!")