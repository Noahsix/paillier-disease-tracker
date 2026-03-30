# Tydzien 1 (20.03 - 26.03): Setup i organizacja

## Cele etapu

- Wspolne zrozumienie idei Pailliera i homomorfii addytywnej.
- Ustalenie architektury klient-serwer.
- Przygotowanie struktury repozytorium pod prace zespolowe.

## Wynik prac

- Utworzono szkielet projektu Python z pakietem w katalogu src.
- Przyjeto SQLite jako baze danych oraz CLI jako pierwszy interfejs.
- Zdefiniowano podzial modulow:
  - crypto: algorytm Pailliera,
  - db: baza danych chorob i zapytania,
  - server: obliczenia na szyfrogramach,
  - client: szyfrowanie/deszyfrowanie i integracja.
- Dodano podstawowa konfiguracje developerska: pyproject.toml, testy pytest, .gitignore.

## Konwencje pracy

- Branching: osobne galezie funkcjonalne per obszar.
- PR wymagany przed scaleniem.
- Wszystkie zmiany krytyczne dla matematyki wspierane testami.
