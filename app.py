from flask import Flask, render_template, request, redirect, session
from game import *
import sqlite3
from functools import wraps
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "blackjack"

# Fungsi Satpam
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

# Fungsi untuk hashing password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Fungsi koneksi database
def get_db_connection():
    conn = sqlite3.connect('blackjack.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route Login
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                         (username, password)).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["coin"] = user["coin"]
            return redirect("/new_game")
        else:
            return "Login Gagal! Periksa kembali username/password."
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        conn = None  # Inisialisasi
        try:
            conn = get_db_connection()
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute('''
                INSERT INTO users (username, password, coin, created_at) 
                VALUES (?, ?, ?, ?)
            ''', (username, password, 1000, now))
            
            conn.commit()
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Username sudah ada!"
        finally:
            if conn:
                conn.close()  # PENTING! Selalu tutup
    return render_template("register.html")
    
@app.route("/new_game")
@login_required
def new_game():
    session["deck"] = buat_deck()
    session["player"] = []
    session["dealer"] = []
    session["taruhan"] = 0
    session.pop("result_shown", None) 
    return redirect("/game")

@app.route("/bet", methods=["POST"])
@login_required
def bet():
    taruhan = int(request.form["taruhan"])
    if taruhan > session["coin"] or taruhan <= 0:
        return redirect("/game")

    session["taruhan"] = taruhan
    session["coin"] -= taruhan
    
    deck = session["deck"]
    session["player"] = [deck.pop(), deck.pop()]
    session["dealer"] = [deck.pop(), deck.pop()]
    session["deck"] = deck
    return redirect("/game")

@app.route("/game")
@login_required
def game():
    player = session.get("player", [])
    total = hitung_total(player) if player else 0
    
    return render_template(
        "game.html",
        player=player,
        dealer=session.get("dealer", []),
        total=total,
        coin=session["coin"],
        bet=session.get("taruhan", 0)
    )

@app.route("/hit", methods=["POST"])
@login_required
def hit():
    deck = session["deck"]
    player = session["player"]
    player.append(deck.pop())
    session["player"] = player
    session["deck"] = deck
    
    # Hitung total dengan aman
    total = hitung_total(player)
    if total > 21:
        return redirect("/result")
    return redirect("/game")

@app.route("/stand")
@login_required
def stand():
    deck = session["deck"]
    dealer = session["dealer"]
    while hitung_total(dealer) < 17:
        dealer.append(deck.pop())
    session["dealer"] = dealer
    return redirect("/result")

@app.route("/double_down", methods=["POST"])
@login_required
def double_down():
    if session["coin"] < session["taruhan"]:
        return redirect("/game")
    
    session["coin"] -= session["taruhan"]
    session["taruhan"] *= 2
    
    deck = session["deck"]
    player = session["player"]
    player.append(deck.pop())
    session["player"] = player
    session["deck"] = deck
    
    if hitung_total(player) > 21:
        return redirect("/result")
    return redirect("/stand")

@app.route("/result")
@login_required
def result():
    # ===== CEK APAKAH ADA DATA GAME =====
    if "player" not in session or not session.get("player"):
        print("⚠️ Tidak ada data player, redirect ke new_game")
        return redirect("/new_game")
    
    # ===== AMBIL DATA DARI SESSION =====
    player_tangan = session.get("player", [])
    dealer_tangan = session.get("dealer", [])
    taruhan = session.get("taruhan", 0)
    
    # ===== HITUNG TOTAL DENGAN FUNGSI DARI GAME.PY =====
    player_total = hitung_total(player_tangan) if player_tangan else 0
    dealer_total = hitung_total(dealer_tangan) if dealer_tangan else 0
    
    # ===== DEBUG LENGKAP =====
    print("="*50)
    print("🔍 DEBUG RESULT:")
    print(f"Player cards: {player_tangan} -> Total: {player_total}")
    print(f"Dealer cards: {dealer_tangan} -> Total: {dealer_total}")
    print(f"Taruhan: {taruhan}")
    print("="*50)
    
    # ===== CEK BLACKJACK =====
    from game import cek_blackjack, hitung_pembayaran
    
    # Gunakan fungsi hitung_pembayaran dari game.py
    hasil = hitung_pembayaran(
        player_tangan, 
        dealer_tangan, 
        taruhan, 
        player_total, 
        dealer_total
    )
    
    msg = hasil['msg']
    pembayaran = hasil['pembayaran']
    
    # ===== UPDATE COIN =====
    if pembayaran > 0:
        session["coin"] += pembayaran
    
    profit = pembayaran - taruhan
    
    # ===== SIMPAN KE DATABASE =====
    conn = None
    try:
        conn = get_db_connection()
        
        # Update coin user
        conn.execute('UPDATE users SET coin = ? WHERE username = ?',
                    (session["coin"], session["username"]))
        
        # Simpan history
        from datetime import datetime
        conn.execute('''
            INSERT INTO history (username, result, bet_amount, profit, player_cards, dealer_cards, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session["username"], 
            msg, 
            taruhan, 
            profit,
            str(player_tangan),
            str(dealer_tangan),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        print(f"✅ Data tersimpan: {msg}, profit: {profit}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    # ===== SIMPAN DATA UNTUK DITAMPILKAN =====
    final_data = {
        "player": player_tangan,
        "dealer": dealer_tangan,
        "player_total": player_total,
        "dealer_total": dealer_total,
        "result": msg,
        "coin": session["coin"],
        "profit": profit,           # <-- TAMBAHKAN PROFIT
        "taruhan": taruhan          # <-- TAMBAHKAN TARUHAN
    }
    
    # ===== PENTING! HAPUS DATA GAME AGAR TIDAK BISA BACK =====
    session.pop("deck", None)
    session.pop("player", None)
    session.pop("dealer", None)
    session.pop("taruhan", None)
    
    # Tandai bahwa result sudah dilihat
    session["result_shown"] = True
    
    print("✅ Data game dihapus dari session, tidak bisa back ke result")
    print(f"💰 Profit: {profit}, Taruhan: {taruhan}")
    
    # ===== RENDER TEMPLATE DENGAN PROFIT =====
    return render_template(
        "result.html", 
        player=final_data["player"], 
        dealer=final_data["dealer"], 
        player_total=final_data["player_total"],
        dealer_total=final_data["dealer_total"],
        result=final_data["result"], 
        coin=final_data["coin"],
        profit=final_data["profit"],        # <-- KIRIM PROFIT
        taruhan=final_data["taruhan"]       # <-- KIRIM TARUHAN
    )

@app.route("/history")
@login_required
def history():
    conn = get_db_connection()
    # Ambil history 20 permainan terakhir untuk user yang login
    history = conn.execute('''
        SELECT * FROM history 
        WHERE username = ? 
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (session["username"],)).fetchall()
    conn.close()
    return render_template("history.html", history=history)

@app.route("/leaderboard")
@login_required
def leaderboard():
    conn = get_db_connection()
    users = conn.execute('SELECT username, coin FROM users ORDER BY coin DESC LIMIT 10').fetchall()
    conn.close()
    return render_template("leaderboard.html", users=users)

@app.route("/profile")
@login_required
def profile():
    target_username = request.args.get('username', session["username"])
    
    conn = get_db_connection()
    
    # Ambil data user - created_at sudah ada
    user = conn.execute('''
        SELECT id, username, coin, created_at 
        FROM users WHERE username = ?
    ''', (target_username,)).fetchone()
    
    if not user:
        return "User tidak ditemukan!", 404
    # Ambil statistik permainan (tambah blackjack count)
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_games,
            SUM(CASE WHEN result LIKE '%Menang%' AND result NOT LIKE '%BLACKJACK%' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result LIKE '%BLACKJACK%' THEN 1 ELSE 0 END) as blackjack_wins,
            SUM(CASE WHEN result LIKE '%Kalah%' OR result LIKE '%Bust%' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN result = 'Seri' OR result LIKE '%Sama-sama Blackjack%' THEN 1 ELSE 0 END) as draws,
            COALESCE(SUM(profit), 0) as total_profit,
            COALESCE(AVG(bet_amount), 0) as avg_bet,
            COALESCE(MAX(profit), 0) as max_win,
            COALESCE(MIN(profit), 0) as max_loss
        FROM history 
        WHERE username = ?
    ''', (target_username,)).fetchone()
    
    # Tambah total wins dengan blackjack
    if stats:
        total_wins = (stats['wins'] or 0) + (stats['blackjack_wins'] or 0)
    else:
        total_wins = 0
    
    # Ambil 5 permainan terakhir
    recent_games = conn.execute('''
        SELECT * FROM history 
        WHERE username = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    ''', (target_username,)).fetchall()
    
    conn.close()
    
    return render_template("profile.html", 
                         user=user, 
                         stats=stats, 
                         total_wins=total_wins,
                         recent_games=recent_games,
                         is_own_profile=(target_username == session["username"]))

@app.route("/admin")
@login_required
def admin_panel():
    # Cek apakah user adalah admin
    if session["username"] != "admin123":
        return "Akses ditolak! Hanya untuk admin.", 403
    
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, coin, created_at FROM users ORDER BY coin DESC').fetchall()
    conn.close()
    
    return render_template("admin.html", users=users)


@app.route("/admin/add_chip", methods=["POST"])
@login_required
def admin_add_chip():
    # Cek apakah user adalah admin
    if session["username"] != "admin123":
        return "Akses ditolak!", 403
    
    username = request.form["username"]
    jumlah = int(request.form["jumlah"])
    
    conn = get_db_connection()
    
    # Cek user exist
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        conn.close()
        return "User tidak ditemukan!", 404
    
    # Tambah chip
    conn.execute('UPDATE users SET coin = coin + ? WHERE username = ?', (jumlah, username))
    conn.commit()
    conn.close()
    
    return redirect("/admin")


@app.route("/admin/delete_user", methods=["POST"])
@login_required
def admin_delete_user():
    # Cek apakah user adalah admin
    if session["username"] != "admin123":
        return "Akses ditolak!", 403
    
    username = request.form["username"]
    
    # Jangan biarkan admin hapus diri sendiri
    if username == "admin123":
        return "Tidak bisa menghapus admin sendiri!", 400
    
    conn = get_db_connection()
    
    # Hapus dari tabel users
    conn.execute('DELETE FROM users WHERE username = ?', (username,))
    # Hapus juga historynya (opsional)
    conn.execute('DELETE FROM history WHERE username = ?', (username,))
    
    conn.commit()
    conn.close()
    
    return redirect("/admin")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        
        # Validasi password baru cocok
        if new_password != confirm_password:
            return "Password baru tidak cocok!", 400
        
        # Validasi panjang password (minimal 4 karakter)
        if len(new_password) < 4:
            return "Password minimal 4 karakter!", 400
        
        # Ambil user dari database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', 
                           (session["username"],)).fetchone()
        
        # Cek password lama
        old_password_hash = hash_password(old_password)
        if user['password'] != old_password_hash:
            conn.close()
            return "Password lama salah!", 400
        
        # Update password baru
        new_password_hash = hash_password(new_password)
        conn.execute('UPDATE users SET password = ? WHERE username = ?',
                    (new_password_hash, session["username"]))
        conn.commit()
        conn.close()
        
        return redirect("/profile?password_changed=1")
    
    return render_template("change_password.html")

@app.route("/claim_bonus")
@login_required
def claim_bonus():
    if session["coin"] <= 0:
        session["coin"] = 500
        conn = get_db_connection()
        conn.execute('UPDATE users SET coin = ? WHERE username = ?', (500, session["username"]))
        conn.commit()
        conn.close()
    return redirect("/new_game")

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)