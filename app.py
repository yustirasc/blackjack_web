import sqlite3
from functools import wraps

# Fungsi Satpam
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect("/") # Usir ke halaman login jika belum ada session
        return f(*args, **kwargs)
    return decorated_function

from flask import Flask, render_template, request, redirect, session
from game import *

app = Flask(__name__)
app.secret_key = "blackjack"

def get_db_connection():
    conn = sqlite3.connect('blackjack.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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
        password = request.form["password"]
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, coin) VALUES (?, ?, ?)',
                         (username, password, 1000))
            conn.commit()
            conn.close()
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Username sudah ada!"
    return render_template("register.html")

@app.route("/new_game")
def new_game():
    session["deck"] = buat_deck()
    session["player"] = []
    session["dealer"] = []
    session["taruhan"] = 0
    return redirect("/game")

@app.route("/bet", methods=["POST"])
@login_required
def bet():
    taruhan = int(request.form["taruhan"])
    if taruhan > session["coin"] or taruhan <= 0:
        return redirect("/game")

    session["taruhan"] = taruhan
    session["coin"] -= taruhan
    
    # Bagikan kartu di sini setelah taruhan dipasang
    deck = session["deck"]
    session["player"] = [deck.pop(), deck.pop()]
    session["dealer"] = [deck.pop(), deck.pop()]
    session["deck"] = deck
    return redirect("/game")

@app.route("/game")
@login_required
def game():
    return render_template(
        "game.html",
        player=session.get("player", []),
        dealer=session.get("dealer", []),
        total=hitung_total(session.get("player", [])),
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
    if hitung_total(player) > 21:
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

@app.route("/result")
@login_required
def result():
    player_total = hitung_total(session["player"])
    dealer_total = hitung_total(session["dealer"])
    msg = ""

    if player_total > 21:
        msg = "Kamu Kalah (Bust)"
    elif dealer_total > 21 or player_total > dealer_total:
        msg = "Kamu Menang!"
        session["coin"] += session["taruhan"] * 2
    elif player_total < dealer_total:
        msg = "Kamu Kalah"
    else:
        msg = "Seri"
        session["coin"] += session["taruhan"]

    # SIMPAN KE DATABASE
    conn = get_db_connection()
    conn.execute('UPDATE users SET coin = ? WHERE username = ?',
                 (session["coin"], session["username"]))
    conn.commit()
    conn.close()

    return render_template("result.html", player=session["player"], 
                           dealer=session["dealer"], result=msg, coin=session["coin"])

@app.route("/leaderboard")
@login_required
def leaderboard():
    conn = get_db_connection()
    # Mengambil semua username dan koin, urutkan dari yang terbesar (DESC)
    users = conn.execute('SELECT username, coin FROM users ORDER BY coin DESC LIMIT 10').fetchall()
    conn.close()
    return render_template("leaderboard.html", users=users)

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

@app.route("/logout")
def logout():
    session.clear() # Menghapus semua data session (username, koin, dll)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)