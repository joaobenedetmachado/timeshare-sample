import re

from src.log import note
from src.models import CONTACT_TYPES, Record
from src.normalize import normalize_address, normalize_name, normalize_phone, normalize_resort

_PHONE_OK = re.compile(r"^\+\d{10,15}(?: x\d{1,6})?$")
_URL_OK = re.compile(r"^https?://", re.I)


def normalize_record(record: Record) -> Record:
    record.name = normalize_name(record.name)
    record.phone_number = normalize_phone(record.phone_number)
    record.address = normalize_address(record.address)
    record.resort = normalize_resort(record.resort)
    record.source = normalize_name(record.source)
    record.source_url = record.source_url.strip()
    record.contact_type = record.contact_type.strip().lower() or "unknown"
    return record


def validate(records: list[Record]) -> list[Record]:
    kept: list[Record] = []
    for record in records:
        reason = _reject_reason(record)
        if reason:
            who = record.name or record.source or "registro"
            note(f"{who} fora: {reason}")
            continue
        kept.append(record)
    return kept


def _reject_reason(record: Record) -> str | None:
    if record.contact_type not in CONTACT_TYPES:
        return f"invalid contact_type {record.contact_type!r}"
    if not _URL_OK.match(record.source_url):
        return "missing source_url"
    if not record.collected_at:
        return "missing collected_at"
    if not record.phone_number or not _PHONE_OK.match(record.phone_number):
        return "phone_number is missing or not normalized"
    if not record.name:
        return "missing name"
    if not record.address:
        return "missing address"
    if not record.resort:
        return "missing resort"
    return None
