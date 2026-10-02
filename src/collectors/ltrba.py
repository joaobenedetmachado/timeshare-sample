import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from src.extract import (
    address_from_page_text,
    combine_resorts,
    member_place,
    published_brand_list,
    published_resorts,
)
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
        offices: dict[str, str] = {}
        records: list[Record] = []
        for member_id, parts in members.items():
            name, phone = _name_and_phone(parts)
            if not name and not phone:
                continue
            source_url = f"{PROFILE_PREFIX}{member_id}" if member_id in profiles else DIRECTORY_URL
            fields = _profile_fields(self.http.get_text(source_url) or "") if member_id in profiles else {}
            biography = fields.get("biography") or _bio(parts)
            resort = combine_resorts(
                published_brand_list(fields.get("brands", "")),
                published_resorts(biography),
            )
            address = member_place(
                fields.get("city", ""),
                fields.get("state", ""),
                fields.get("country", ""),
            )
            if not resort or not address:
                filled_resort, filled_address = _fill_from_company_site(self.http, _email(parts), offices)
                resort = resort or filled_resort
                address = address or filled_address
            if not resort or not address:
                note(f"{name or 'card'} has no resort or address, left out")
                continue
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


def _profile_fields(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    def value(placeholder: str) -> str:
        node = soup.find("input", attrs={"placeholder": placeholder})
        if node is not None and node.get("value"):
            return re.sub(r"\s+", " ", node["value"]).strip()
        area = soup.find("textarea", attrs={"placeholder": placeholder})
        if area is None:
            return ""
        return re.sub(r"\s+", " ", area.get_text("\n", strip=True)).strip()

    return {
        "city": value("City"),
        "state": value("State"),
        "country": value("Country"),
        "biography": value("Biography"),
        "brands": value("Timeshare Brands"),
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


def _fill_from_company_site(
    http: HttpClient,
    email: str,
    cache: dict[str, str],
) -> tuple[str, str]:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    if not domain or domain in _FREE_EMAIL:
        return "", ""
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
    return published_resorts(specialty), address_from_page_text(page_text)


_COMPANY_PATHS = ("/", "/contact-us", "/contact", "/contact-me", "/terms-of-use")


def _company_text(http: HttpClient, domain: str) -> str:
    pages: list[str] = []
    for index, path in enumerate(_COMPANY_PATHS):
        html = http.get_text(f"https://{domain}{path}", quiet=True)
        if not html:
            if index + 1 < len(_COMPANY_PATHS):
                fallback(f"{domain}{path}", _COMPANY_PATHS[index + 1])
            continue
        text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
        found = address_from_page_text(text)
        if found and re.search(r"\d", found):
            return text
        pages.append(text)
    for text in pages:
        if address_from_page_text(text) or published_resorts(text):
            return text
    return ""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
