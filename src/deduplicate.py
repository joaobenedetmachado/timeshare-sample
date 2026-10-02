import re

from src.models import Record


def deduplicate(records: list[Record]) -> list[Record]:
    """Drop repeats of the same contact at the same resort.

    A shared office line stays once per person and once per resort. Two
    listings for different resorts are not duplicates of each other.
    """
    best: dict[tuple[str, str, str], Record] = {}
    order: list[tuple[str, str, str]] = []
    for record in records:
        key = _key(record)
        current = best.get(key)
        if current is None:
            best[key] = record
            order.append(key)
            continue
        if _score(record) > _score(current):
            best[key] = record
    return [best[key] for key in order]


def _key(record: Record) -> tuple[str, str, str]:
    phone = re.sub(r"\D", "", record.phone_number.split(" x", 1)[0])
    return (phone, record.name.casefold(), record.resort.casefold())


def _score(record: Record) -> int:
    return sum(
        bool(value)
        for value in (
            record.name,
            record.phone_number,
            record.address,
            record.resort,
            record.source_url,
        )
    )
