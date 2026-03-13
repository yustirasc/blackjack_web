# reset_db.py
import sqlite3
import hashlib
from datetime import datetime

print("🚀 Mulai reset database...")

# Konek ke database
conn = sqlite3.connect('blackjack.db')
cursor = conn.cursor()

# Hapus tabel lama kalau ada
cursor.execute('DROP TABLE IF EXISTS users')
cursor.execute('DROP TABLE IF EXISTS history')
print("✅ Tabel lama dihapus")

# Buat tabel users
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        coin INTEGER DEFAULT 1000,
        created_at TEXT
    )
''')
print("✅ Tabel users dibuat")

# Buat tabel history
cursor.execute('''
    CREATE TABLE history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        result TEXT NOT NULL,
        bet_amount INTEGER,
        profit INTEGER,
        player_cards TEXT,
        dealer_cards TEXT,
        created_at TEXT
    )
''')
print("✅ Tabel history dibuat")

# Hash function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Tambah user contoh
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# User admin
cursor.execute('''
    INSERT INTO users (username, password, coin, created_at) 
    VALUES (?, ?, ?, ?)
''', ('admin', hash_password('admin123'), 5000, now))

# User player
cursor.execute('''
    INSERT INTO users (username, password, coin, created_at) 
    VALUES (?, ?, ?, ?)
''', ('player', hash_password('player123'), 1000, now))

print("✅ User contoh ditambahkan")

conn.commit()
conn.close()

print("🎉 DATABASE BERHASIL DI-RESET!")
print("📝 Login dengan:")
print("   - admin / admin123")
print("   - player / player123")