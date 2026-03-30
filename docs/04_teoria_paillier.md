# Podstawy teoretyczne schematu Pailliera

## Parametry i klucze

1. Wybieramy dwie duze liczby pierwsze p i q.
2. Liczymy:
   - n = p * q
   - lambda = lcm(p - 1, q - 1)
   - g = n + 1
3. Definiujemy funkcje L(u) = (u - 1) / n.
4. Liczymy mu = (L(g^lambda mod n^2))^-1 mod n.

Klucz publiczny: (n, g)
Klucz prywatny: (lambda, mu)

## Szyfrowanie i deszyfrowanie

Dla wiadomosci m z zakresu [0, n):

- losujemy r wzglednie pierwsze z n,
- szyfrogram:
  c = g^m * r^n mod n^2.

Deszyfrowanie:

- m = L(c^lambda mod n^2) * mu mod n.

## Homomorfia addytywna

Jesli c1 = Enc(m1), c2 = Enc(m2), to:

- c1 * c2 mod n^2 = Enc(m1 + m2).

Dodatkowo, dla stalej k:

- c^k mod n^2 = Enc(k * m).

W projekcie te dwie wlasnosci sa wykorzystane do liczenia statystyk chorob na serwerze bez ujawniania danych pacjentow.
