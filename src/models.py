from dataclasses import dataclass

FIELDNAMES = [
    "name",
    "phone_number",
    "address",
    "resort",
    "source",
    "source_url",
    "collected_at",
    "contact_type",
]

CONTACT_TYPES = ("owner", "agent", "company", "unknown")


@dataclass
class Record:
    name: str = ""
    phone_number: str = ""
    address: str = ""
    resort: str = ""
    source: str = ""
    source_url: str = ""
    collected_at: str = ""
    contact_type: str = "unknown"

    def as_row(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in FIELDNAMES}
