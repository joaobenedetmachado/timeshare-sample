import html
import re

# Brands and resort names that appear as proper nouns on the public pages.
_LEADING = (
    r"Marriott(?:'s|’s)?|Hilton(?:\s+Grand Vacations)?|Hyatt(?:\s+Residence)?|"
    r"Westin|Sheraton|Disney|Wyndham|WorldMark|Starwood|Vistana|"
    r"Breckenridge(?:\s+Grand Vacations)?|Four Seasons(?:\s+Residence)?|"
    r"HGVC|Westgate|Ritz-Carlton|Holiday Inn(?:\s+Club Vacations)?|"
    r"Sands of Kahana|The Whaler|Vacation Internationale|Club Wyndham|"
    r"Resorts West|Pahio|Sunterra Pacific"
)
_TRAIL_WORDS = {
    "sales",
    "executive",
    "owner",
    "hotel",
    "rewards",
    "honors",
    "we",
    "having",
    "member",
    "clubs",
    "ownership",
    "ownerships",
    "resales",
    "resale",
    "products",
    "groups",
    "properties",
    "along",
    "with",
    "for",
    "over",
    "directly",
    "and",
    "worldwide",
    "timeshares",
    "timeshare",
    "colorado",
    "florida",
    "california",
    "nevada",
    "hawaii",
    "utah",
    "spain",
    "since",
}
_HISTORY = re.compile(
    r"\b(?:purchased my first|joined the|years of working with|entered the timeshare|storefront location)\b",
    re.I,
)
_BRAND = re.compile(rf"\b(?:{_LEADING})\b", re.I)
_NEXT_WORD = re.compile(r"(?:\s+(?:de|of|at)\s+|\s+)([A-Z][A-Za-z0-9'’\-]*)")
_ACRONYMS = {"HGVC", "VRI", "RCI", "VI"}
_USA = {"usa", "us", "u.s.", "u.s.a.", "united states", "united states of america"}
_STATE_NAME = (
    "North Carolina|North Dakota|South Carolina|South Dakota|West Virginia|"
    "New Hampshire|New Jersey|New Mexico|New York|Rhode Island|"
    "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
    "Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|"
    "Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|"
    "Nebraska|Nevada|Ohio|Oklahoma|Oregon|Pennsylvania|Tennessee|Texas|Utah|Vermont|"
    "Virginia|Washington|Wisconsin|Wyoming"
)
_TIGHT_ADDRESS = re.compile(
    r"(?P<street>\d{2,6}\s+[A-Za-z0-9.'\- ]{2,50}?\b"
    r"(?i:Drive|Street|Avenue|Boulevard|Road|Lane|Circle|Court|Way|Dr|Rd|St|Ave|Blvd|Ln|Ct)\.?)"
    r"(?P<suite>,?\s*Suite\s*[A-Za-z0-9\-]+)?"
    r",?\s*(?P<city>(?:[A-Z][a-z]+\s*){1,3}?),\s*"
    rf"(?P<state>{_STATE_NAME}|[A-Z]{{2}}),?\s*(?P<zip>\d{{5}})\b"
)


def published_resorts(text: str) -> str:
    found: list[str] = []
    sentences = re.split(r"(?<=[.!])\s+", text or "")
    for sentence in sentences:
        if _HISTORY.search(sentence):
            continue
        found.extend(_scan_resorts(sentence))
    if not any(item.casefold().startswith("hilton") for item in found):
        for sentence in sentences:
            if _HISTORY.search(sentence):
                continue
            if re.search(r"\bHilton\b", sentence, flags=re.I):
                found.append("Hilton")
                break
    return "; ".join(_prefer_longer(found)[:8])


def published_brand_list(text: str) -> str:
    """Brands named in a profile field, split on commas and line breaks."""
    raw = html.unescape(text or "")
    raw = re.sub(r"^include:\s*", "", raw.strip(), flags=re.I)
    found: list[str] = []
    for part in re.split(r"[\n,;]+", raw):
        part = re.sub(r"\s+and many more.*$", "", part, flags=re.I).strip(" .")
        if not part or re.search(r"\b(?:if your|please ask|many more)\b", part, re.I):
            continue
        found.extend(_scan_resorts(part))
    return "; ".join(_prefer_longer(found)[:8])


def combine_resorts(*chunks: str) -> str:
    items: list[str] = []
    for chunk in chunks:
        items.extend(part.strip() for part in (chunk or "").split(";") if part.strip())
    return "; ".join(_prefer_longer(items)[:8])


def published_place(text: str, company_label: str = "") -> str:
    """A stated office or 'licensed in City, State'. Markets and license states are not a place."""
    del company_label
    return _office(text or "")


def member_place(city: str, state: str, country: str) -> str:
    """City and state from a profile form. A state alone, or an 'Offices:' note, is not an address."""
    city_text = _region_token(city)
    state_text = _region_token(state)
    country_text = _region_token(country)
    if not city_text:
        return ""
    if len(state_text) == 2 and state_text.isalpha():
        state_text = state_text.upper()
    parts = [city_text]
    if state_text:
        parts.append(state_text)
    if country_text and country_text.casefold() not in _USA:
        parts.append(country_text)
    return ", ".join(parts)


def address_from_page_text(text: str) -> str:
    """A postal street with city and ZIP. License states and bare city names are left out."""
    flat = re.sub(r"\s+", " ", text or "")
    for match in _TIGHT_ADDRESS.finditer(flat):
        before = flat[max(0, match.start() - 40) : match.start()]
        if re.search(r"marriott|hilton|resort|club|vacation", before, re.I):
            continue
        street = re.sub(r"\s+", " ", match.group("street")).strip(" ,")
        suite = match.group("suite")
        if suite:
            street = f"{street}, {re.sub(r'^,\s*', '', suite).strip(' ,')}"
        city = re.sub(r"\s+", " ", match.group("city")).strip()
        state = match.group("state")
        if len(state) == 2:
            state = state.upper()
        return f"{street}, {city}, {state} {match.group('zip')}"
    return ""


def _trim(name: str) -> str:
    text = re.sub(r"\s+", " ", name).strip(" ,;.-")
    words = text.split()
    while words and words[-1].casefold().strip(".'’") in _TRAIL_WORDS:
        words.pop()
    text = " ".join(words).strip(" ,'’")
    text = re.sub(r"['’]s$", "", text).strip()
    if len(text) < 3 or text.casefold() in {"the", "at", "in"}:
        return ""
    return text


def _scan_resorts(text: str) -> list[str]:
    found: list[str] = []
    for match in _BRAND.finditer(text):
        words = [_title_word(match.group(0))]
        rest = text[match.end() :]
        while len(words) < 7:
            nxt = _NEXT_WORD.match(rest)
            if not nxt:
                break
            words.append(_title_word(nxt.group(1)))
            rest = rest[nxt.end() :]
        name = _trim(" ".join(words))
        if name and _brand_count(name) <= 1:
            found.append(name)
    return found


def _title_word(word: str) -> str:
    bare = word.strip("().")
    letters = [char for char in bare if char.isalpha()]
    if letters and all(char.isupper() for char in letters) and bare not in _ACRONYMS and len(letters) > 3:
        return word.capitalize()
    return word


def _region_token(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip(" ,")
    if not text or re.search(r"\d|#|\boffice\b", text, re.I):
        return ""
    return text


def _office(text: str) -> str:
    match = re.search(r"office is located at (?:the )?(.+?)(?: and we\b|[.]|$)", text, flags=re.I)
    if match:
        return _tidy_place(match.group(1))
    match = re.search(
        r"\b(?:licensed(?:\s+\w+){0,4}\s+in|broker in|based in)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*"
        r"(Florida|California|Colorado|Nevada|Arizona|Washington|Hawaii|Utah)\b",
        text,
    )
    if match:
        return f"{match.group(1)}, {match.group(2)}"
    return ""


def _tidy_place(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip(" ,;.")
    text = re.sub(r"^downtown\b", "Downtown", text, flags=re.I)
    text = re.sub(r"\s+and we are open for business every day$", "", text, flags=re.I)
    return text.strip(" ,;.")


def _brand_count(name: str) -> int:
    brands = re.findall(
        r"\b(?:marriott|hilton|hyatt|westin|sheraton|disney|wyndham|starwood|vistana|hgvc)\b",
        name,
        flags=re.I,
    )
    return len(brands)


def _fold(text: str) -> str:
    return re.sub(r"\bclubs\b", "club", text.casefold())


def _prefer_longer(items: list[str]) -> list[str]:
    ordered: list[str] = []
    for item in items:
        key = _fold(item)
        if any(key == _fold(current) for current in ordered):
            continue
        if any(f" {key} " in f" {_fold(current)} " or _fold(current).startswith(key + " ") for current in ordered):
            continue
        ordered = [
            current
            for current in ordered
            if not key.startswith(_fold(current) + " ")
        ]
        ordered.append(item)
    return ordered
