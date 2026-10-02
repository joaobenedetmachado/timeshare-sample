import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.http import HttpClient
from src.log import fallback, note
from src.models import Record

INDEX_URL = "https://www.sellmytimesharenow.com/timeshares-for-sale/"
_DETAIL_HREF = re.compile(r"/timeshares/index/content/details/AdNumber/\d+/sale/?")


class SmtnCollector:
    """Public SellMyTimeshareNow listing cards.

    Detail pages label some ads "for sale by owner" but do not publish the
    owner's name or phone. The call-now number belongs to the marketplace.
    """

    source = "SellMyTimeshareNow"

    def __init__(self, http: HttpClient, max_listings: int = 8) -> None:
        self.http = http
        self.max_listings = max_listings

    def collect(self) -> list[Record]:
        html = self.http.get_text(INDEX_URL)
        if not html:
            return []

        detail_urls = _detail_urls(html)
        records: list[Record] = []
        for url in detail_urls[: self.max_listings]:
            page = self.http.get_text(url)
            if not page:
                continue
            record = _parse_detail(page, url)
            if record:
                records.append(record)
        logger.info("SellMyTimeshareNow parsed %s listing pages", len(records))
        return records


def _detail_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    urls: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not _DETAIL_HREF.search(href):
            continue
        absolute = urljoin(INDEX_URL, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        urls.append(absolute)
    return urls


def _parse_detail(html: str, url: str) -> Record | None:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    resort = re.sub(r"\s+Timeshare for Sale\b.*$", "", title, flags=re.I).strip()
    if not resort:
        logger.info("No resort title on %s", url)
        return None

    phone_node = soup.select_one("span.phone-number")
    phone = phone_node.get_text(" ", strip=True) if phone_node else ""
    page_text = soup.get_text(" ", strip=True)
    name = "SellMyTimeshareNow" if "SellMyTimeshareNow" in page_text else ""
    return Record(
        name=name,
        phone_number=phone,
        address=_listing_address(soup),
        resort=resort,
        source="SellMyTimeshareNow",
        source_url=url,
        collected_at=_now(),
        contact_type="company" if name else "unknown",
    )


def _listing_address(soup: BeautifulSoup) -> str:
    candidates: list[str] = []
    for node in soup.select("div.location"):
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip(" |")
        if text:
            candidates.append(text)
    numbered = [item for item in candidates if re.search(r"\d", item)]
    chosen = max(numbered, key=len) if numbered else (candidates[0] if candidates else "")
    parts = [part.strip() for part in chosen.split(",") if part.strip()]
    unique: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(part)
    return ", ".join(unique)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
