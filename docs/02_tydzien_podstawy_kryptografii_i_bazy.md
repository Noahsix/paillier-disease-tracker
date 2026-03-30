# Tydzien 2 (27.03 - 02.04): Podstawy kryptografii i bazy danych

## Zakres wykonany

### Osoba 1 - implementacja Pailliera

- Generacja kluczy publicznego i prywatnego.
- Szyfrowanie pojedynczych liczb calkowitych (zakres [0, n)).
- Deszyfrowanie szyfrogramow do wartosci jawnych.

### Osoba 2 - baza chorob i dane

- Zaprojektowana struktura SQLite:
  - tabela diseases (nazwa choroby + numeric_code),
  - tabela patients,
  - tabela diagnoses (flaga jawna + flaga zaszyfrowana).
- Dodane mapowanie nazwa choroby -> kod liczbowy.
- Przygotowane dane testowe i zapytania do pobierania szyfrogramow.

### Osoba 3 - dokumentacja

- Utworzony szkielet dokumentacji projektu i opisu teoretycznego.
- Rozpisane role i odpowiedzialnosci w kolejnych tygodniach.

### Lider - spiecie modulow

- Integracja pustych modulow do dzialajacego szkieletu aplikacji.
- Przygotowanie punktow wejscia CLI pod dalsza integracje.
