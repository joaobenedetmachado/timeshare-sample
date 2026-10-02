import csv
from pathlib import Path

from src.models import FIELDNAMES, Record


def export_csv(records: list[Record], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda record: (record.source, record.name, record.resort, record.source_url))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in ordered:
            writer.writerow(record.as_row())
