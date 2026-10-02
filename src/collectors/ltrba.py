import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from src.extract import address_from_page_text, published_place, published_resorts
from src.http import HttpClient
from src.log import fallback, note
from src.models import Record

DIRECTORY_URL = "https://www.licensedtimeshareresalebrokers.org/members-all"
PROFILE_PREFIX = "https://www.licensedtimeshareresalebrokers.org/SiteMembers/"
_LABELS = {"phone:", "email:"}
_FREE_EMAIL = {"me.com", "icloud.com", "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
_RICH_TEXT = re.compile(
    r'id="comp-[^"]+__([0-9a-f-]{36})"[^>]*data-testid="richTextElement">(.*?)</div>',
    re.I | re.S,
)


class LtrbaCollector:
    """Licensed Timeshare Resale Brokers Association public member directory."""

    source = "LTRBA"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(self) -> list[Record]:
        html = self.http.get_text(DIRECTORY_URL)
        if not html:
            return []

        collected_at = _now()
        profiles = set(re.findall(r"/SiteMembers/([0-9a-f-]{36})", html, flags=re.I))
        members = _group_members(html)
        labels = _company_labels(html)
        offices: dict[str, str] = {}
        records: list[Record] = []
        for member_id, parts in members.items():
            name, phone = _name_and_phone(parts)
            if not name and not phone:
                continue
            bio = _bio(parts)
            label = labels.get(member_id, "")
            resort = published_resorts(bio)
            address = published_place(bio, label)
            email = _email(parts)
            if not resort or not address or _broad(address):
                filled_resort, filled_address = _fill_from_company_site(
                    self.http, email, offices, resort, address
                )
                resort = resort or filled_resort
                if filled_address and (
                    not address
                    or (_broad(address) and re.search(r"\b[A-Z]{2}\s+\d{5}\b", filled_address))
                ):
                    address = filled_address
            if not resort or not address:
                note(f"{name or 'ficha'} sem resort ou endereço, deixada de fora")
                continue
            source_url = f"{PROFILE_PREFIX}{member_id}" if member_id in profiles else DIRECTORY_URL
            records.append(
                Record(
                    name=name,
                    phone_number=phone,
                    address=address,
                    resort=resort,
                    source=self.source,
                    source_url=source_url,
                    collected_at=collected_at,
                    # Named person on the licensed-broker directory, not a confirmed owner.
                    contact_type="agent",
                )
            )
        return records


def _group_members(html: str) -> dict[str, list[str]]:
    members: dict[str, list[str]] = {}
    for match in _RICH_TEXT.finditer(html):
        text = BeautifulSoup(match.group(2), "html.parser").get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            members.setdefault(match.group(1), []).append(text)
    return members


def _name_and_phone(parts: list[str]) -> tuple[str, str]:
    phone_index = next((index for index, part in enumerate(parts) if _looks_like_phone(part)), None)
    name_parts = parts if phone_index is None else parts[:phone_index]
    names = [
        part
        for part in name_parts
        if part.casefold() not in _LABELS and "@" not in part and len(part) <= 40
    ]
    phone = "" if phone_index is None else parts[phone_index]
    return " ".join(names[:3]), phone


def _broad(address: str) -> bool:
    return address.casefold() in {
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
    }


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 10 and "@" not in value


def _bio(parts: list[str]) -> str:
    long_parts = [part for part in parts if len(part) > 80]
    return long_parts[-1] if long_parts else ""


def _email(parts: list[str]) -> str:
    for part in parts:
        match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", part)
        if match:
            return match.group(0)
    return ""


def _company_labels(html: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    pattern = re.compile(r'alt="([^"]+)"[\s\S]{0,2500}?__([0-9a-f-]{36})', re.I)
    for match in pattern.finditer(html):
        label = re.sub(r"\s+", " ", match.group(1)).strip()
        if "logo" in label.casefold() or "basic black" in label.casefold():
            continue
        labels.setdefault(match.group(2), label)
    return labels


def _fill_from_company_site(
    http: HttpClient,
    email: str,
    cache: dict[str, str],
    resort: str,
    address: str,
) -> tuple[str, str]:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    if not domain or domain in _FREE_EMAIL:
        return resort, address
    page_text = cache.get(domain)
    if page_text is None:
        page_text = _company_text(http, domain)
        cache[domain] = page_text
    if not page_text:
        return "", ""
    specialty = " ".join(
        part.strip()
        for part in re.split(r"[.\n]", page_text)
        if re.search(r"speciali[sz]", part, flags=re.I) and len(part) < 240
    )
    return published_resorts(specialty), address_from_page_text(page_text) or published_place(page_text)


def _company_text(http: HttpClient, domain: str) -> str:
    pages: list[str] = []
    for path in ("/", "/contact-us", "/contact"):
        html = http.get_text(f"https://{domain}{path}")
        if not html:
            continue
        pages.append(BeautifulSoup(html, "html.parser").get_text("\n", strip=True))
    for text in pages:
        found = address_from_page_text(text)
        if found and re.search(r"\d", found):
            return text
    for text in pages:
        if address_from_page_text(text) or published_resorts(text):
            return text
    return ""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
