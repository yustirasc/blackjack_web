import sqlite3

def init_db():
    conn = sqlite3.connect('blackjack.db')
    cursor = conn.cursor()
    # Membuat tabel users jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            coin INTEGER DEFAULT 1000
        )
    ''')
    conn.commit()
    conn.close()
    print("Database berhasil dibuat!")

if __name__ == "__main__":
    init_db()