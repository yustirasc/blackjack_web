import random

def buat_deck():
    deck = []
    nilai_kartu = list(range(2, 11)) + ['J', 'Q', 'K', 'A']
    jenis_kartu = ['♦','♣','♠','♥']

    for nilai in nilai_kartu:
        for jenis in jenis_kartu:
            deck.append((str(nilai), jenis))

    random.shuffle(deck)
    return deck


def nilai_kartu(kartu):
    nilai = kartu[0]

    if nilai in ['J','Q','K']:
        return 10
    elif nilai == 'A':
        return 11
    else:
        return int(nilai)


def hitung_total(tangan):
    """
    Hitung total nilai kartu dengan penanganan As yang benar
    """
    if not tangan or len(tangan) == 0:
        return 0
    
    total = 0
    as_count = 0
    
    # Hitung total awal
    for k in tangan:
        nilai = nilai_kartu(k)
        if nilai == 11:  # As
            as_count += 1
            total += 11
        else:
            total += nilai
    
    # Sesuaikan As jika total > 21
    while total > 21 and as_count > 0:
        total -= 10
        as_count -= 1
    
    return total


def cek_blackjack(tangan):
    """
    Cek apakah tangan adalah Blackjack (A + 10/J/Q/K di 2 kartu pertama)
    """
    if not tangan or len(tangan) != 2:
        return False
    
    kartu1 = tangan[0][0]
    kartu2 = tangan[1][0]
    
    as_ada = (kartu1 == 'A' or kartu2 == 'A')
    sepuluh_ada = (kartu1 in ['10', 'J', 'Q', 'K'] or kartu2 in ['10', 'J', 'Q', 'K'])
    
    return as_ada and sepuluh_ada


def hitung_pembayaran(player_tangan, dealer_tangan, taruhan, player_total, dealer_total):
    """
    Hitung pembayaran dengan aturan Blackjack (3:2 untuk Blackjack)
    """
    player_blackjack = cek_blackjack(player_tangan)
    dealer_blackjack = cek_blackjack(dealer_tangan)
    
    # Player Blackjack, dealer tidak Blackjack
    if player_blackjack and not dealer_blackjack:
        return {
            'msg': 'BLACKJACK! Kamu Menang! (3:2)',
            'pembayaran': int(taruhan * 2.5)  # 1:1 + bonus 0.5
        }
    
    # Dealer Blackjack, player tidak Blackjack
    elif dealer_blackjack and not player_blackjack:
        return {
            'msg': 'Dealer Blackjack! Kamu Kalah',
            'pembayaran': 0
        }
    
    # Sama-sama Blackjack
    elif player_blackjack and dealer_blackjack:
        return {
            'msg': 'Sama-sama Blackjack! Seri',
            'pembayaran': taruhan  # Kembali modal
        }
    
    # Tidak ada Blackjack - pakai aturan biasa
    else:
        if player_total > 21:
            return {'msg': 'Kamu Kalah (Bust)', 'pembayaran': 0}
        elif dealer_total > 21 or player_total > dealer_total:
            return {'msg': 'Kamu Menang!', 'pembayaran': taruhan * 2}
        elif player_total < dealer_total:
            return {'msg': 'Kamu Kalah', 'pembayaran': 0}
        else:
            return {'msg': 'Seri', 'pembayaran': taruhan}