# Architektura symulacji klient-serwer (chmura)

## Role komponentow

- Klient:
  - generuje klucze,
  - szyfruje dane pacjentow,
  - odszyfrowuje tylko wynik koncowy.
- Serwer (cloud analytics):
  - pobiera szyfrogramy z bazy,
  - agreguje je homomorficznie,
  - nie posiada klucza prywatnego.
- SQLite:
  - przechowuje slownik chorob,
  - trzyma dane pacjentow,
  - trzyma szyfrogramy flag chorob.

## Przeplyw danych

1. Klient dodaje rekord pacjenta (0/1 dla chorob) i szyfruje kazda flage.
2. Szyfrogramy sa zapisane do bazy przez warstwe repozytorium.
3. Serwer pobiera szyfrogramy dla wybranej choroby.
4. Serwer mnozy szyfrogramy modulo n^2, uzyskujac zaszyfrowana sume.
5. Klient pobiera zaszyfrowany wynik i deszyfruje liczbe wystapien.

## Co serwer widzi

- Nazwy chorob i identyfikatory rekordow.
- Szyfrogramy pojedynczych flag.
- Brak dostepu do klucza prywatnego i wartosci jawnych flag.
