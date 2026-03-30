# Tydzien 3 (03.04 - 09.04): Wlasciwa homomorfia

## Zakres wykonany

### Osoba 1 - operacje homomorficzne

- Dodawanie homomorficzne szyfrogramow (sumowanie wartosci zaszyfrowanych).
- Mnozenie zaszyfrowanej wartosci przez stala.

### Osoba 2 - zapytania i dane szyfrowane

- Metody repozytorium pobierajace szyfrogramy dla wybranej choroby.
- Przygotowanie skryptow przeplywu danych do obliczen po stronie serwera.

### Osoba 3 - interfejs

- Pierwszy interfejs CLI:
  - setup,
  - add-patient,
  - seed-demo,
  - count,
  - list-diseases,
  - show-encrypted.
- Wstepna implementacja GUI (Tkinter):
  - setup/load konfiguracji,
  - dodawanie pacjentow,
  - zliczanie choroby po stronie serwera,
  - podglad szyfrogramow per pacjent.

### Lider - integracja klient-serwer

- Symulacja klient-serwer:
  - klient szyfruje i zapisuje dane,
  - serwer oblicza wynik na szyfrogramach bez klucza prywatnego,
  - klient odszyfrowuje finalny wynik.
- Dodane testy integracyjne potwierdzajace zgodnosc wyniku homomorficznego i klasycznego.

## Przyklad przeplywu

1. Klient dodaje pacjenta i szyfruje flagi chorob.
2. Serwer pobiera szyfrogramy z bazy dla wybranej choroby.
3. Serwer wykonuje iloczyn szyfrogramow, otrzymujac zaszyfrowana sume.
4. Klient deszyfruje wynik i prezentuje liczbe wystapien choroby.
