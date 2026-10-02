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
_RESORT_NAME = re.compile(
    rf"\b((?:{_LEADING})(?:(?:\s+(?:de|of|at)\s+|\s+)[A-Z][A-Za-z0-9'’-]*){{0,6}})"
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
_PLACE_TAIL = re.compile(
    r"^(?:Aruba|Florida|Hawaii|California|Arizona|Colorado|Utah|Nevada|Washington(?: State)?|"
    r"North & South Carolina|North Carolina|South Carolina|Caribbean|Spain|Maui|"
    r"United Kingdom|Costa del Sol|Cabo San Lucas|Palm Springs|Orlando|Breckenridge|"
    r"Park City|Lahaina|Carlsbad|Scottsdale|Jackson Hole|Costa Rica|Punta Mita|"
    r"Marbella|Phuket|Gatlinburg|Las Vegas)$",
    re.I,
)


def published_resorts(text: str) -> str:
    found: list[str] = []
    for match in _RESORT_NAME.finditer(text or ""):
        name = _trim(match.group(1))
        if name and _brand_count(name) <= 1:
            found.append(name)
    # "Hilton Resorts" is still a stated brand family; keep Hilton if nothing longer exists.
    if re.search(r"\bHilton\b", text or "", flags=re.I) and not any(item.casefold().startswith("hilton") for item in found):
        found.append("Hilton")
    return "; ".join(_prefer_longer(found)[:8])


def published_place(text: str, company_label: str = "") -> str:
    office = _office(text or "")
    if office:
        return office
    regions = _regions(text or "") + _label_places(company_label or "")
    return "; ".join(_prefer_longer(regions)[:4])


def address_from_page_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip(" ,|") for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    for index, line in enumerate(lines):
        if not re.search(
            r"\d{2,6}\s+\S.{0,50}\b(?:Dr|Drive|Rd|Road|St|Street|Ave|Avenue|Blvd|Boulevard|Way|Lane|Ln|Circle|Ct)\b",
            line,
            re.I,
        ):
            continue
        if re.search(r"marriott|hilton|resort|club|vacation", line, re.I):
            continue
        window = " ".join(lines[index : index + 3])
        city_match = re.search(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\s+(\d{5})\b",
            window,
        )
        if city_match and city_match.group(1).casefold().startswith(("road", "drive", "street", "johnson")):
            city_match = re.search(
                r"\b([A-Z][a-z]+),\s*([A-Z]{2})\s+(\d{5})\b",
                window,
            )
        street = re.sub(r"\s+", " ", line).strip(" ,")
        if city_match:
            city = f"{city_match.group(1)}, {city_match.group(2)} {city_match.group(3)}"
            if city.casefold() not in street.casefold():
                return f"{street}, {city}"
        return street

    for line in lines:
        for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\b", line):
            city, state = match.group(1), match.group(2)
            if state not in {"OK", "FL", "CA", "UT", "NV", "HI", "CO", "AZ", "WA", "NY", "TX"}:
                continue
            if re.search(r"timeshare|resale|realty|vacation|club|marriott|hilton|disney", city, re.I):
                continue
            return f"{city}, {state}"

    licenses = re.findall(
        r"\b(Utah|Nevada|Florida|California|Hawaii|Colorado|Arizona|Washington)\s+License",
        text or "",
        re.I,
    )
    return "; ".join(_prefer_longer(licenses))


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


def _office(text: str) -> str:
    match = re.search(r"office is located at (?:the )?(.+?)(?: and we\b|[.]|$)", text, flags=re.I)
    if match:
        return _tidy_place(match.group(1))
    match = re.search(r"storefront location in (downtown [A-Za-z .'-]+)", text, flags=re.I)
    if match:
        return _tidy_place(match.group(1))
    match = re.search(r"(Costa del Sol in Spain)", text, flags=re.I)
    if match:
        return "Costa del Sol, Spain"
    match = re.search(
        r"\b(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*"
        r"(Florida|California|Colorado|Nevada|Arizona|Washington|Hawaii|Utah)\b",
        text,
    )
    if match:
        return f"{match.group(1)}, {match.group(2)}"
    match = re.search(r"\bBreckenridge,?\s+Colorado\b", text, flags=re.I)
    if match:
        return "Breckenridge, Colorado"
    return ""


def _regions(text: str) -> list[str]:
    found: list[str] = []
    match = re.search(
        r"(?:locations in the|areas of interest are|ski locations like)\s+([^.!]+)",
        text,
        flags=re.I,
    )
    if match:
        found.extend(_split_places(match.group(1)))
    match = re.search(r"licensed(?:\s+\w+){0,4}\s+in both\s+([^.!]+)", text, flags=re.I)
    if match:
        found.extend(_split_places(match.group(1)))
    if re.search(r"\bWashington State\b", text):
        found.append("Washington")
    if re.search(r"\b(?:State of Hawaii|in Hawaii)\b", text, flags=re.I):
        found.append("Hawaii")
    if re.search(r"\bCalifornia Licensed\b|\bin California\b", text):
        found.append("California")
    if re.search(r"\bNevada\b", text) and re.search(r"\b(?:licensed|salesperson|broker)\b", text, flags=re.I):
        found.append("Nevada")
    if re.search(r"\blicensed Florida\b", text, flags=re.I):
        found.append("Florida")
    if re.search(r"\bMaui\b", text):
        found.append("Maui")
    if re.search(r"\bCabo San Lucas\b", text):
        found.append("Cabo San Lucas")
    for match in re.finditer(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([A-Z]{2})\b", text):
        found.append(f"{match.group(1)}, {match.group(2)}")
    return found


def _label_places(label: str) -> list[str]:
    found: list[str] = []
    if re.search(r"\bUK\b", label):
        found.append("United Kingdom")
    if re.search(r"\bSpain\b", label, flags=re.I):
        found.append("Spain")
    return found


def _split_places(chunk: str) -> list[str]:
    chunk = re.sub(r"\s+&\s+", ", ", chunk)
    chunk = re.sub(r"\s+and\s+", ", ", chunk, flags=re.I)
    places: list[str] = []
    for part in chunk.split(","):
        place = _tidy_place(part)
        if _PLACE_TAIL.match(place) or "," in place:
            places.append(place)
    return places


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
