# Paillier Disease Tracker

Projekt demonstruje obliczenia statystyk medycznych na zaszyfrowanych danych z uzyciem kryptosystemu Pailliera.

## Zakres wykonany (tygodnie 1-4)

- Tydzien 1: setup repozytorium, struktura aplikacji, konwencje i dokumentacja startowa.
- Tydzien 2: implementacja kluczy, szyfrowania, deszyfrowania, projekt bazy chorob i mapowania nazw.
- Tydzien 3: operacje homomorficzne, zapytania po szyfrogramach, interfejs CLI i pierwsza integracja klient-serwer.
- Tydzien 4: docelowa logika COUNT/SUM po stronie serwera chmurowego, rozszerzone testy jednostkowe i wizualizacja przeplywu w GUI.

## Architektura (symulacja klient-serwer)

- Klient: generuje klucze, szyfruje dane, odszyfrowuje wynik koncowy.
- Serwer chmurowy: pobiera szyfrogramy z bazy i wykonuje obliczenia homomorficzne bez klucza prywatnego.
- Baza SQLite: przechowuje slownik chorob, pacjentow i zaszyfrowane flagi wystapien chorob.

## Szybki start

1. Instalacja lokalna:

   ```bash
   pip install -e .[dev]
   ```

2. Inicjalizacja projektu (klucze + baza + katalog chorob):

   ```bash
   paillier-tracker setup
   ```

3. Dodanie danych demo:

   ```bash
   paillier-tracker seed-demo
   ```

4. Zliczanie choroby na serwerze (COUNT/SUM na szyfrogramach):

   ```bash
   paillier-tracker count --disease grypa --show-steps
   ```

5. Testy:

   ```bash
   pytest
   ```

6. Wstepny interfejs GUI:

   ```bash
   paillier-tracker-gui
   ```

   Jesli komenda nie jest widoczna w PATH, uzyj launchera z virtualenv:

   ```bash
   .venv\\Scripts\\paillier-tracker-gui.exe
   ```

Po uruchomieniu GUI zacznij od przycisku `Setup new` (nowa baza + nowe klucze)
lub `Load existing` (istniejace pliki).

W GUI dostepny jest panel wizualizacji procesu:
`dane jawne -> szyfrogram -> wynik homomorficzny -> odszyfrowany wynik`.

Szczegolowe opisy sa w katalogu docs.
