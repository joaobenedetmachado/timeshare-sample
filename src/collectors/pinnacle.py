import re
from datetime import datetime, timezone
from html import unescape

from src.http import HttpClient
from src.log import fallback
from src.models import Record

# Public state-search ids. Each page is a brokerage result list, not an owner directory.
STATE_PAGES = (
    (10, "Florida"),
    (12, "Hawaii"),
    (29, "Nevada"),
    (41, "South Carolina"),
)
_CARD = re.compile(
    r'class="resorthead">([^<]+)</span>(.*?)(?=class="resorthead"|</form>|$)',
    re.I | re.S,
)
_LISTING_ID = re.compile(r"listingid=(\d+)", re.I)
_TOLL_FREE = re.compile(r"Toll Free:\s*([0-9][0-9.\-() ]{8,})", re.I)
_OFFICE = re.compile(
    r"(\d{3,6}\s+[A-Za-z0-9.'\- ]+,\s*Suite\s*[A-Za-z0-9\-]+,\s*Box\s*\d+)"
    r"\s*(?:•|·|&bull;|&#8226;|&#149;)\s*"
    r"([A-Za-z .'-]+,\s*[A-Z]{2}\s+\d{5})",
    re.I,
)


class PinnacleCollector:
    """Public Pinnacle Vacations resale results.

    The only phone and street address on these pages are the brokerage office.
    Owner identity is not published, so every row is contact_type=company.
    """

    source = "Pinnacle Vacations"

    def __init__(self, http: HttpClient, max_resorts: int = 12) -> None:
        self.http = http
        self.max_resorts = max_resorts

    def collect(self) -> list[Record]:
        records: list[Record] = []
        seen: set[str] = set()
        for state_id, state_name in STATE_PAGES:
            if len(records) >= self.max_resorts:
                break
            url = (
                "https://www.pinnaclevacations.com/search-results.aspx"
                f"?prevpage=state-search.aspx&stateid={state_id}"
            )
            html = self.http.get_text(url)
            if not html:
                continue
            page_records = _parse_results(html, url, state_name)
            for record in page_records:
                key = record.resort.casefold()
                if not key or key in seen:
                    continue
                seen.add(key)
                records.append(record)
                if len(records) >= self.max_resorts:
                    break
        return records


def _parse_results(html: str, url: str, state_name: str) -> list[Record]:
    text = unescape(html)
    name = "Pinnacle Vacations" if re.search(r"Pinnacle Vacations", text, re.I) else ""
    phone_match = _TOLL_FREE.search(text)
    phone = phone_match.group(1).strip() if phone_match else ""
    address_match = _OFFICE.search(html)
    address = ""
    if address_match:
        address = f"{address_match.group(1)}, {address_match.group(2)}"

    collected_at = _now()
    records: list[Record] = []
    for match in _CARD.finditer(html):
        resort = unescape(match.group(1))
        resort = re.sub(r"\s+", " ", resort).strip()
        if not resort or not _LISTING_ID.search(match.group(2)):
            continue
        records.append(
            Record(
                name=name,
                phone_number=phone,
                address=address,
                resort=resort,
                source="Pinnacle Vacations",
                source_url=url,
                collected_at=collected_at,
                contact_type="company" if name else "unknown",
            )
        )
    if not records:
        fallback(state_name, "the next state")
    return records


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
