# update.py
import sqlite3
from datetime import datetime

conn = sqlite3.connect('blackjack.db')
cursor = conn.cursor()

# Cek dan tambah kolom created_at
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'created_at' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET created_at = ?", (now,))
    print("✅ Kolom created_at berhasil ditambahkan!")
else:
    print("✅ Kolom created_at sudah ada")

conn.commit()
conn.close()
print("✨ Update selesai!")