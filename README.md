# Лабораторна робота №5 — спортивні результати

Рішення для індивідуального варіанта №9 з ЛР №3: потоковий імпорт CSV спортивних результатів, перевірка записів, tolerant/strict політика, статистика, окремий CSV помилок та атомарний JSON export.

## Запуск

Потрібен Python 3.11+ і PyYAML:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
sports-streaming
```

Або з кореня проєкту без встановлення пакета:

```powershell
$env:PYTHONPATH = "src"
py -m sports_streaming.main
```

`config.yaml` керує шляхами, допустимими видами спорту/категоріями, діапазонами числового результату, часовим форматом, режимом валідації та рівнем журналювання. Шляхи відносні до робочої директорії.

## Режими

- `tolerant`: помилковий рядок потрапляє у `output/invalid_records.csv`, пишеться warning, обробка продовжується.
- `strict`: перший некоректний запис завершує імпорт із `RecordValidationError`; JSON формується у тимчасовому файлі й не підміняє попередній результат до успіху.

## Структура

```text
config.yaml
 data/sports_results.csv
 src/sports_streaming/
   config.py exceptions.py exporters.py logging_config.py main.py models.py
   readers.py services.py validators.py analytics.py batches.py filters.py
 output/ logs/
```

`--limit N` демонструє обмеження потоку через `itertools.islice`. Додатково доступні `rank_results` (обмежений top-N), `pairwise_changes` (itertools.pairwise), `batches` (пакети фіксованого розміру) та `filter_results`.

## Git

From the project folder, initialize the repository once, then stage and commit the lab files:

```powershell
git init
git add .
git commit -m "Implement lab 5 sports results importer"
```

If Git asks for your identity, set it once with `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`. The project folder is delivered without an initialized Git repository.
