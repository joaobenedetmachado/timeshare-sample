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
    record.resort = choose_resort(normalize_resort(record.resort))
    record.source = normalize_name(record.source)
    record.source_url = record.source_url.strip()
    record.contact_type = record.contact_type.strip().lower() or "unknown"
    return record


def validate(records: list[Record]) -> list[Record]:
    kept: list[Record] = []
    for record in records:
        reason = _reject_reason(record)
        if reason:
            who = record.name or record.source or "record"
            note(f"{who} dropped: {reason}")
            continue
        kept.append(record)
    return kept


def _reject_reason(record: Record) -> str | None:
    if record.contact_type not in CONTACT_TYPES:
        return "invalid contact type"
    if not _URL_OK.match(record.source_url):
        return "missing source url"
    if not record.collected_at:
        return "missing collected_at"
    if not record.phone_number or not _PHONE_OK.match(record.phone_number):
        return "invalid phone"
    if not record.name:
        return "missing name"
    if not record.address or not address_is_specific(record.address):
        return "address is not a specific place"
    if not record.resort or not resort_is_specific(record.resort):
        return "resort is not one property"
    return None


_REGIONS = {
    "florida",
    "california",
    "nevada",
    "hawaii",
    "utah",
    "colorado",
    "washington",
    "spain",
    "maui",
    "united kingdom",
    "uk",
    "caribbean",
    "aruba",
    "multi-destination",
    "outside us",
}

_BARE_BRANDS = {
    "marriott",
    "hilton",
    "hyatt",
    "disney",
    "westin",
    "sheraton",
    "starwood",
    "vistana",
    "hgvc",
    "westgate",
    "wyndham",
    "worldmark",
    "sunterra",
    "sunterra pacific",
    "holiday inn",
    "pahio",
    "marriott points",
    "marriott vacation club",
    "breckenridge grand vacations",
    "hilton grand vacation club",
    "hilton grand vacations",
    "hilton grand vacations club",
    "marriott destination points",
    "breckenridge resorts",
}


def address_is_specific(address: str) -> bool:
    text = address.strip()
    folded = text.casefold()
    if not text or ";" in text or folded in _REGIONS or "multi-destination" in folded:
        return False
    if re.search(r"\d", text):
        return True
    parts = [part.strip() for part in text.split(",")]
    if not 2 <= len(parts) <= 3:
        return False
    if parts[0].casefold() in _REGIONS:
        return False
    if any(part.casefold() in {"multi-destination", "outside us"} for part in parts):
        return False
    place = r"[A-Za-z][A-Za-z .'-]{1,40}"
    return all(re.fullmatch(place, part) for part in parts)


def choose_resort(resort: str) -> str:
    """Keep one property name. A brand list is not a resort."""
    parts = [part.strip() for part in resort.split(";") if part.strip()]
    specific = [part for part in parts if _one_property(part)]
    if len(specific) == 1:
        return specific[0]
    return ""


def _one_property(name: str) -> bool:
    folded = name.casefold()
    if not name or ";" in name or folded in _BARE_BRANDS or "multi-destination" in folded:
        return False
    return True


def resort_is_specific(resort: str) -> bool:
    return _one_property(resort.strip())
