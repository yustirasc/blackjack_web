import sqlite3

def delete_user(username):
    conn = sqlite3.connect('blackjack.db')
    cursor = conn.cursor()
    
    # Hapus user
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    
    if cursor.rowcount > 0:
        print(f"User '{username}' berhasil dihapus!")
    else:
        print(f"User '{username}' tidak ditemukan.")
    
    # Tampilkan sisa user
    cursor.execute("SELECT username, coin FROM users")
    users = cursor.fetchall()
    print("\nSisa user di database:")
    for user in users:
        print(f"- {user[0]}: {user[1]} coins")
    
    conn.close()

if __name__ == "__main__":
    username = input("Masukkan username yang mau dihapus: ")
    delete_user(username)