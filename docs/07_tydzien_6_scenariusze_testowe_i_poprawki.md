# Tydzien 6 (24.04 - 30.04): Scenariusze testowe i poprawki

## Cele etapu

- Przejscie przez 6 scenariuszy testowych end-to-end.
- Domkniecie bugfixingu i cleanupu kodu.
- Dopracowanie GUI (funkcjonalnie i wizualnie) oraz poprawa podgladu operacji.

## 6 scenariuszy testowych (status)

Wszystkie scenariusze maja automatyzacje testowa i przeszly poprawnie.

### Scenariusz 1: Setup projektu i katalog chorob

- Zakres: inicjalizacja bazy i slownika chorob.
- Test: `test_scenario_01_setup_and_catalog_initialization`.
- Oczekiwany wynik: katalog chorob istnieje, liczba pacjentow = 0.
- Status: PASS.

### Scenariusz 2: Reczne dodawanie pacjentow i zliczanie choroby

- Zakres: dodanie rekordow i obliczenie COUNT/SUM po stronie serwera.
- Test: `test_scenario_02_manual_insert_and_encrypted_count`.
- Oczekiwany wynik: wynik odszyfrowany == referencja jawna.
- Status: PASS.

### Scenariusz 3: Seed demo i podglad flow operacji

- Zakres: przygotowanie danych demo i wizualizacja przebiegu `plain -> ciphertext -> homomorphic -> decrypted`.
- Test: `test_scenario_03_demo_seed_and_flow_preview`.
- Oczekiwany wynik: liczba wierszy flow zgadza sie z liczba rekordow, wynik koncowy poprawny.
- Status: PASS.

### Scenariusz 4: Duzy wolumen danych + walidacja zbiorcza

- Zakres: hurtowe wygenerowanie 1000 rekordow oraz walidacja dla wszystkich chorob.
- Test: `test_scenario_04_bulk_dataset_and_full_validation`.
- Oczekiwany wynik: wszystkie choroby przechodza walidacje.
- Status: PASS.

### Scenariusz 5: Wykrywanie naruszenia integralnosci danych

- Zakres: celowe rozjechanie pola jawnego i ciphertext w bazie.
- Test: `test_scenario_05_integrity_check_detects_tampering`.
- Oczekiwany wynik: raport walidacji wykrywa blad (FAIL).
- Status: PASS.

### Scenariusz 6: Benchmark kryptografii dla wielu kluczy

- Zakres: pomiar czasu keygen/encrypt/decrypt/homomorphic dla wielu key size.
- Test: `test_scenario_06_benchmark_for_multiple_key_sizes`.
- Oczekiwany wynik: poprawna struktura wynikow i dodatnie czasy.
- Status: PASS.

## Bugfixing i cleanup

### Bugfix: ochrona przed nieznana choroba

- Dodano jawna walidacje nazwy choroby przed liczeniem i walidacja.
- Efekt: brak falszywych pozytywow dla nieistniejacej choroby.

### Cleanup: porzadkowanie warstwy repozytorium

- Wspolna walidacja diagnoz i wydzielony helper do wstawiania pacjenta.
- Dodana operacja hurtowa `add_patients_bulk` do zapisu w jednej transakcji.

## Dopracowanie GUI

### Zakres funkcjonalny

Dodane i/lub rozbudowane:

- Seed bulk (liczba rekordow, seed, prefix, batch size).
- Walidacja pojedynczej choroby i walidacja wszystkich chorob.
- Benchmarki kryptograficzne uruchamiane z poziomu GUI.
- Eksport raportu benchmarku do Markdown.
- Odswiezenie mapowania chorob z widokiem tabelarycznym.

### Zakres UX i podgladu operacji

- Przebudowa GUI do layoutu opartego o zakladki: Projekt, Pacjenci i dane, Analityka i walidacja, Benchmarki, Log.
- Rozszerzony panel analityczny:
  - podsumowanie wynikow (rows, encrypted/decrypted/plain, status),
  - tabela flow,
  - tabela encrypted rows,
  - raport walidacji,
  - timeline przebiegu pipeline.
- Dodany pasek statusu i bardziej czytelna stylizacja interfejsu.

## Wynik koncowy tygodnia 6

- Testy automatyczne: 27/27 PASS.
- Scenariusze testowe: 6/6 PASS.
- GUI: dopracowane wizualnie i funkcjonalnie, obejmuje funkcje z tygodni 1-6.
