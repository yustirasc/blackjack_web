# init_db.py
import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('blackjack.db')
    cursor = conn.cursor()
    
    # Hapus tabel lama jika ada (opsional - kalau mau reset total)
    cursor.execute('DROP TABLE IF EXISTS history')
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # Buat tabel users
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            coin INTEGER DEFAULT 1000
        )
    ''')
    
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
    
    # Tambahkan user contoh
    cursor.execute('''
        INSERT INTO users (username, password, coin) 
        VALUES (?, ?, ?)
    ''', ('admin', hash_password('admin123'), 5000))
    
    cursor.execute('''
        INSERT INTO users (username, password, coin) 
        VALUES (?, ?, ?)
    ''', ('player', hash_password('player123'), 1000))
    
    conn.commit()
    conn.close()
    print("Database berhasil dibuat!")
    print("\nUser tersedia:")
    print("- admin (password: admin123) - 5000 coins")
    print("- player (password: player123) - 1000 coins")
    print("\nTabel yang tersedia:")
    print("- users (untuk data user)")
    print("- history (untuk riwayat permainan)")

if __name__ == "__main__":
    init_db()