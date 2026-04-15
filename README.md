# Paillier Disease Tracker

Projekt demonstruje obliczenia statystyk medycznych na zaszyfrowanych danych z uzyciem kryptosystemu Pailliera.

## Zakres wykonany (tygodnie 1-6)

- Tydzien 1: setup repozytorium, struktura aplikacji, konwencje i dokumentacja startowa.
- Tydzien 2: implementacja kluczy, szyfrowania, deszyfrowania, projekt bazy chorob i mapowania nazw.
- Tydzien 3: operacje homomorficzne, zapytania po szyfrogramach, interfejs CLI i pierwsza integracja klient-serwer.
- Tydzien 4: docelowa logika COUNT/SUM po stronie serwera chmurowego, rozszerzone testy jednostkowe i wizualizacja przeplywu w GUI.
- Tydzien 5: benchmarki czasu szyfrowania/deszyfrowania/homomorfii dla wielu dlugosci klucza, hurtowe seedowanie tysiecy rekordow oraz automatyczna walidacja wynikow homomorficznych.
- Tydzien 6: formalne scenariusze testowe (6/6), bugfixing i cleanup oraz mocna rozbudowa GUI (walidacja, seed-bulk, benchmarki, lepszy podglad pipeline).

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

   Uwaga: ponowne uruchomienie `setup` generuje nowe klucze i czysci dane
   pacjentow/diagnoz, aby uniknac mieszania szyfrogramow z roznych par kluczy.

3. Dodanie danych demo:

   ```bash
   paillier-tracker seed-demo
   ```

4. Zliczanie choroby na serwerze (COUNT/SUM na szyfrogramach):

   ```bash
   paillier-tracker count --disease grypa --show-steps
   ```

5. Seedowanie duzego wolumenu danych (np. 5000 rekordow):

   ```bash
   paillier-tracker seed-bulk --patients 5000 --seed 42
   ```

6. Automatyczna walidacja (homomorfia vs referencja jawna SQL):

   ```bash
   paillier-tracker validate
   ```

7. Benchmarki kryptografii dla wielu kluczy:

   ```bash
   paillier-tracker benchmark-crypto --key-sizes 256,512,1024
   ```

8. Testy:

   ```bash
   pytest
   ```

9. Wstepny interfejs GUI:

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

GUI obejmuje takze funkcje tygodnia 5/6:

- seed-bulk z parametrami wolumenu,
- walidacja pojedynczej choroby i wszystkich chorob,
- benchmark kryptografii dla wielu dlugosci klucza,
- eksport raportu benchmarku do Markdown.

GUI jest zbudowane na `ttkbootstrap` (nowoczesny framework UI dla Tkinter),
z obsluga dynamicznej zmiany motywu bez restartu aplikacji.

Szczegolowe opisy sa w katalogu docs.

## Instrukcja poprawnej obslugi GUI (walidacja)

Stosuj zawsze jedna spojna pare plikow: DB + keys.

1. Ustaw pola `DB path` i `Keys path` w zakladce Projekt.
2. Wybierz jeden tryb startu:
   - nowy projekt: kliknij `Setup new` (generuje nowe klucze; jesli sa stare rekordy pacjentow, zostana wyczyszczone),
   - istniejacy projekt: kliknij `Load existing` (ladujesz istniejace klucze i baze bez rotacji kluczy).
3. Dodaj dane (`Seed demo`, `Run seed-bulk` albo reczne `Add patient`).
4. Przejdz do zakladki Analityka i walidacja.
5. Wybierz chorobe i kliknij `Count encrypted`, a nastepnie `Validate selected` lub `Validate all`.
6. Odczytaj status w kafelku `Validation` i w tabeli `Validation report`.

Najczestsze powody niepowodzenia walidacji w GUI:

- mieszanie kluczy i danych z roznych projektow (inny `keys.json` niz ten, ktory szyfrowal rekordy),
- przypadkowa rotacja kluczy przez `Setup new` po dodaniu danych (stare rekordy sa wtedy czyszczone),
- walidacja na pustej bazie po setupie (wyniki 0 sa poprawne, ale nie odzwierciedlaja danych, bo ich nie ma).

Wskazowka: po zmianie `DB path` lub `Keys path` aplikacja automatycznie przeladuje kontekst przy kolejnej operacji.

## Instrukcja poprawnej obslugi (setup, dane, walidacja)

Najwazniejsza zasada: zawsze pracuj na spojnej parze plikow bazy i kluczy.

1. Uzyj jednej pary plikow i podawaj je we wszystkich komendach:

   ```bash
   paillier-tracker --db-path data/projekt.db --keys-path data/projekt_keys.json setup
   paillier-tracker --db-path data/projekt.db --keys-path data/projekt_keys.json seed-bulk --patients 5000 --seed 42
   paillier-tracker --db-path data/projekt.db --keys-path data/projekt_keys.json validate
   ```

2. Pamietaj o skladni CLI: `--db-path` i `--keys-path` to argumenty globalne,
   wiec musza wystapic przed subkomenda (`setup`, `seed-bulk`, `validate`, `count`).

3. Jesli uruchomisz `setup` ponownie na tej samej bazie:
   - zostanie wygenerowana nowa para kluczy,
   - dane pacjentow i diagnoz zostana wyczyszczone automatycznie,
   - katalog chorob pozostaje dostepny.

4. Jesli `validate` zwraca `status=False`:
   - sprawdz, czy we wszystkich komendach uzywasz tej samej pary `--db-path` i `--keys-path`,
   - sprawdz, czy argumenty globalne nie zostaly podane po subkomendzie,
   - wykonaj sekwencje od nowa: `setup` -> `seed-demo` lub `seed-bulk` -> `validate`.

Przy poprawnej sekwencji walidacja powinna zakonczyc sie wynikiem `all_valid=True`.
