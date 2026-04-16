
import sqlite3
import os

db_path = os.path.join("backend", "foodsquare.db")
if not os.path.exists(db_path):
    print("Database not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT userName, password, roles FROM User")
    users = cursor.fetchall()
    print("Users in DB:")
    for user in users:
        print(f"Username: {user[0]}, Role: {user[2]}")
    conn.close()
