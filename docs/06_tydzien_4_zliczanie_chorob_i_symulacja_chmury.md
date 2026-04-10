# Tydzien 4 (10.04 - 16.04): Zliczanie chorob i symulacja chmury

## Zakres wykonany

### Osoba 1 - matematyka i testy jednostkowe

- Rozszerzone testy jednostkowe operacji Pailliera:
  - roundtrip szyfrowanie/deszyfrowanie,
  - homomorphic add/add_many,
  - mnozenie przez stala,
  - przypadki brzegowe (puste kolekcje, stale ujemne, niepoprawny zakres danych).
- Dodane testy walidacyjne dla blednych danych wejsciowych (zakres plaintext/ciphertext, randomizer r).

### Osoba 2 - logika serwera COUNT/SUM bez klucza prywatnego

- Dodana docelowa agregacja serwerowa COUNT/SUM na szyfrogramach dla wybranej choroby.
- Serwer operuje tylko na ciphertextach i kluczu publicznym.
- Dla binarnych flag chorob (0/1):
  - COUNT przypadkow = SUM flag,
  - wynik pozostaje zaszyfrowany do momentu odszyfrowania po stronie klienta.
- Dodany model wyniku serwerowego zawierajacy szyfrowane COUNT/SUM oraz liczbe rekordow.

### Osoba 3 - wizualizacja procesu w GUI

- Rozbudowane GUI o panel procesu:
  - dane jawne,
  - szyfrogramy,
  - wynik homomorficzny,
  - odszyfrowany wynik.
- Dodana tabela per pacjent pokazujaca przebieg `plain -> ciphertext`.
- Rozszerzone logi GUI o informacje COUNT/SUM i walidacje wyniku.

### Lider - integracja klient <-> serwer chmurowy

- Spiety przeplyw end-to-end:
  - klient szyfruje i zapisuje dane,
  - serwer chmurowy liczy COUNT/SUM homomorficznie,
  - klient odszyfrowuje i waliduje wynik z referencja jawna.
- Rozszerzona warstwa klienta o model wyniku COUNT/SUM oraz obiekt przeplywu do wizualizacji.
- Zaktualizowany CLI do raportowania COUNT/SUM oraz trybu pokazania krokow procesu.

## Efekt tygodnia 4

Projekt zawiera teraz kompletna symulacje obliczen chmurowych na szyfrogramach dla zliczania chorob,
z testami jednostkowymi i czytelna wizualizacja procesu w interfejsie GUI.
