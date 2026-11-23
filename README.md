# Cache Simulator

Symulator pamięci podręcznej cache tworzony w ramach pracy inżynierskiej.
Projekt służy do obserwowania wpływu geometrii cache i polityki zastępowania
na wyniki dostępu do pamięci.

> **Status: w trakcie rozwoju**
>
> Interfejs i zakres funkcji mogą się zmieniać. Obecna wersja jest działającym
> prototypem CLI, a nie finalnym wydaniem.

## Obecne możliwości

- mapowanie `direct-mapped`, `set-associative` i `fully-associative`,
- konfigurowalny rozmiar cache, rozmiar bloku, asocjatywność i szerokość adresu,
- polityki zastępowania: **LRU**, **FIFO**, **LFU** i **Random**,
- operacje odczytu (`R`) i zapisu (`W`),
- obsługa linii dirty oraz zliczanie dirty eviction,
- statystyki: hits, misses, evictions i hit rate,
- wykonanie śladu krok po kroku z rozbiciem adresu na tag, indeks i offset,
- porównanie kilku wariantów architektury cache,
- parser plików śladu oraz testy jednostkowe.

## Wymagania

- Python **3.14 lub nowszy**,
- [uv](https://docs.astral.sh/uv/) (zalecane) albo standardowe środowisko
  wirtualne Pythona.

## Uruchomienie

Po sklonowaniu repozytorium i przejściu do jego katalogu:

```bash
uv sync
uv run cache-simulator
```

Domyślne uruchomienie wczytuje `examples/demo.trace`, pokazuje przebieg
symulacji dla konfiguracji 64 B / 16 B / 2-way / LRU, a następnie porównuje
wybrane warianty.

Przykładowe uruchomienia:

```bash
# Własny ślad i zwykłe podsumowanie
uv run cache-simulator --trace examples/demo.trace

# Szczegółowy przebieg krok po kroku
uv run cache-simulator --trace examples/demo.trace --step-by-step

# Własna konfiguracja
uv run cache-simulator \
  --cache-size 256 \
  --block-size 16 \
  --associativity 4 \
  --policy lfu \
  --address-bits 16
```

Pełna lista opcji:

```bash
uv run cache-simulator --help
```

## Format śladu

Każda niepusta linia pliku `.trace` opisuje jedną operację:

```text
R 0x0000
W 0x0044
```

`R` oznacza odczyt, a `W` zapis. Adres można zapisać dziesiętnie lub
szesnastkowo (`0x...`). Komentarze rozpoczynające się od `#` są ignorowane.
Przykładowy ślad znajduje się w pliku [`examples/demo.trace`](examples/demo.trace).

## Struktura projektu

```text
src/cache_simulator/
├── core/
│   ├── address.py       # dekodowanie adresu
│   ├── cache.py         # główna logika cache
│   ├── config.py        # konfiguracja i geometria
│   ├── policies.py      # polityki zastępowania
│   ├── simulator.py     # wykonywanie śladu
│   └── trace.py         # operacje i zdarzenia
├── io/
│   └── trace_parser.py  # wczytywanie śladów
└── main.py              # interfejs CLI
tests/                   # testy jednostkowe
examples/                # przykładowe dane wejściowe
```

## Testy i formatowanie

```bash
uv run pytest
uv run ruff check .
```

## Planowany rozwój

Zakres będzie ewoluował wraz z pracą nad projektem. Planowane są między innymi
dalszy rozwój interfejsu użytkownika, rozbudowa wizualizacji oraz dopracowanie
modelu i raportowania symulacji.
