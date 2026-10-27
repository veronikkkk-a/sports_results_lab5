"""Reproducible reliability and eager-vs-streaming experiments for the report."""
import csv
import json
import tempfile
import tracemalloc
import time
from dataclasses import replace
from pathlib import Path
from sports_streaming.config import load_config
from sports_streaming.exceptions import ConfigurationError, DataExportError, RecordValidationError
from sports_streaming.exporters import export_json
from sports_streaming.models import SportsResult
from sports_streaming.services import ImportStatistics, import_results

ROOT = Path(__file__).parent
FIELDS = ["athlete", "sport", "result", "category", "timestamp"]
ROW = ["Runner Example", "running", "12.5", "senior", "2026-10-20T09:15:00"]

def generate_csv(path: Path, count: int, invalid_every: int = 0) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        for index in range(count):
            row = [f"Athlete {index}", *ROW[1:]]
            if invalid_every and index % invalid_every == invalid_every - 1:
                row[2] = "bad-result"
            writer.writerow(row)

def measure(path: Path, eager: bool) -> tuple[float, float, int]:
    tracemalloc.start()
    started = time.perf_counter()
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if eager:
            count = len(list(reader))
        else:
            count = sum(1 for _ in reader)
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / (1024 * 1024), count

def run() -> None:
    cfg = load_config(ROOT / "config.yaml")
    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        source = temp / "strict_tolerant.csv"
        generate_csv(source, 1010, invalid_every=101)
        tolerant = replace(cfg, input_path=source, mode="tolerant")
        stats = ImportStatistics()
        errors: list[dict[str, object]] = []
        accepted = sum(1 for _ in import_results(tolerant, stats, errors))
        print(f"TOLERANT total={stats.total} valid={stats.valid} invalid={stats.invalid} yielded={accepted}")
        strict = replace(cfg, input_path=source, mode="strict")
        strict_stats = ImportStatistics()
        try:
            sum(1 for _ in import_results(strict, strict_stats, []))
        except RecordValidationError as error:
            print(f"STRICT total_seen={strict_stats.total} valid={strict_stats.valid} invalid={strict_stats.invalid} stopped={error.line_number}")

        protected = temp / "protected.json"
        protected.write_text('[{"previous": true}]\n', encoding="utf-8")
        timestamp = __import__("datetime").datetime(2026, 10, 20, 9, 15)
        def broken_records():
            yield SportsResult("A", "running", 12.0, "senior", timestamp)
            raise RuntimeError("simulated export interruption")
        try:
            export_json(broken_records(), protected)
        except RuntimeError:
            pass
        preserved = protected.read_text(encoding="utf-8") == '[{"previous": true}]\n'
        leftovers = list(temp.glob(".protected.json.*.tmp"))
        print(f"ATOMIC previous_preserved={preserved} temporary_files={len(leftovers)}")

        for name, body in (("missing", ""), ("malformed", "input: ["),
                           ("missing-key", "input:\\n  path: data.csv\\n")):
            candidate = temp / f"{name}.yaml"
            candidate.write_text(body, encoding="utf-8")
            try:
                load_config(candidate)
            except ConfigurationError as error:
                print(f"CONFIG {name}=controlled:{type(error.__cause__).__name__ if error.__cause__ else 'validation'}")
            except Exception as error:
                print(f"CONFIG {name}=unexpected:{type(error).__name__}")
        missing = temp / "absent.yaml"
        try:
            load_config(missing)
        except ConfigurationError as error:
            print(f"CONFIG absent=controlled:{type(error.__cause__).__name__}")

        print("BENCHMARK records eager_seconds eager_peak_MB streaming_seconds streaming_peak_MB")
        for count in (10_000, 100_000, 500_000):
            dataset = temp / f"bench_{count}.csv"
            generate_csv(dataset, count)
            eager_time, eager_mem, _ = measure(dataset, True)
            stream_time, stream_mem, _ = measure(dataset, False)
            print(f"{count} {eager_time:.4f} {eager_mem:.3f} {stream_time:.4f} {stream_mem:.3f}")

if __name__ == "__main__":
    run()
