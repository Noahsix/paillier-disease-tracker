# Tydzien 6: Dane z testow wydajnosciowych

Data pomiaru: 2026-04-15
Srodowisko: Windows, Python 3.13, virtualenv projektu

## Metodyka

### Benchmark kryptografii

- Klucze: 128, 256, 512 bit.
- Iteracje:
  - encrypt: 100,
  - decrypt: 100,
  - homomorphic_add_many: 60,
  - homomorphic_mul_const: 60,
  - batch dla add_many: 32.

### Benchmark przeplywu aplikacyjnego

- Klucz: 256 bit.
- Wolumen: 1000, 3000, 5000 rekordow pacjentow.
- Mierzone kroki:
  - seed bulk,
  - pojedyncze liczenie choroby (`count_and_sum_disease`),
  - walidacja wszystkich chorob (`validate_all_disease_sums`).

## Wyniki: kryptografia

| Key size | Keygen [ms] | Encrypt avg [ms] | Decrypt avg [ms] | Add_many avg [ms] | Mul_const avg [ms] |
| --- | ---: | ---: | ---: | ---: | ---: |
| 128 | 0.933 | 0.042 | 0.040 | 0.009 | 0.001 |
| 256 | 3.324 | 0.218 | 0.212 | 0.023 | 0.001 |
| 512 | 16.772 | 1.364 | 1.370 | 0.082 | 0.005 |

## Wyniki: przeplyw danych i walidacja

| Wolumen rekordow | Seed bulk [s] | Count [ms] | Validate all [ms] | Validation status |
| --- | ---: | ---: | ---: | --- |
| 1000 | 1.013 | 7.194 | 23.372 | True |
| 3000 | 2.860 | 16.938 | 51.873 | True |
| 5000 | 4.630 | 23.645 | 76.809 | True |

## Wnioski

- Czas operacji kryptograficznych rosnie wraz z dlugoscia klucza zgodnie z oczekiwaniami.
- Dla 512 bit obserwujemy wyrazny wzrost kosztu encrypt/decrypt wzgledem 128 i 256 bit.
- Operacje homomorficzne po ciphertextach sa relatywnie szybkie, ale rowniez skaluja sie z rozmiarem klucza.
- Warstwa aplikacyjna skaluje sie liniowo dla seed bulk oraz prawie liniowo dla walidacji.
- Walidacja utrzymuje poprawny status (`True`) dla wszystkich testowanych wolumenow.

## Rekomendacje do dalszej analizy

- Dodac serie pomiarowe z powtorzeniami (np. 5 uruchomien) i raportowac srednia + odchylenie standardowe.
- Rozszerzyc test wolumenowy do 10k-50k rekordow dla granicznej oceny czasu walidacji.
- Rozwazyc osobny raport porownawczy dla key size 768 i 1024 bit.
