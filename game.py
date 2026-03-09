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
    total = sum(nilai_kartu(k) for k in tangan)

    as_count = sum(1 for k in tangan if k[0] == 'A')

    while total > 21 and as_count > 0:
        total -= 10
        as_count -= 1

    return total