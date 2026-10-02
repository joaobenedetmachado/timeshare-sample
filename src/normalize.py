import html
import re

_SMALL_WORDS = {"at", "of", "and", "the", "on", "de", "da", "do", "for"}


def normalize_name(raw: str) -> str:
    text = _clean_text(raw)
    text = re.sub(r"\s+", " ", text).strip(" ,;|-")
    if len(text) > 80:
        return ""
    return text


def normalize_phone(raw: str) -> str:
    """Return E.164 when the number is unambiguous, otherwise an empty string."""
    if not raw or not raw.strip():
        return ""

    text = _clean_text(raw)
    # A label such as "or Text 801-..." still contains one number. A second
    # number joined with " or " is a different line; keep only the first.
    if re.match(r"^or\b", text, flags=re.I):
        chunk = text
    else:
        chunk = re.split(r"\s+or\s+", text, maxsplit=1, flags=re.I)[0]

    extension_match = re.search(r"(?:x|ext\.?|extension)\s*(\d{1,6})\s*$", chunk, flags=re.I)
    extension = extension_match.group(1) if extension_match else ""
    head = chunk[: extension_match.start()] if extension_match else chunk
    international = "+" in head or bool(re.match(r"\s*00", head))
    digits = re.sub(r"\D", "", head)
    if digits.startswith("00"):
        digits = digits[2:]
        international = True

    if digits.startswith("44") and len(digits) > 2 and digits[2] == "0":
        digits = "44" + digits[3:]
        international = True

    if international or (len(digits) > 11 and not digits.startswith("1")):
        if not 10 <= len(digits) <= 15:
            return ""
        formatted = f"+{digits}"
    else:
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            return ""
        formatted = f"+1{digits}"

    if extension:
        formatted = f"{formatted} x{extension}"
    return formatted


def normalize_address(raw: str) -> str:
    text = _clean_text(raw)
    if not text:
        return ""
    text = text.replace("•", ",").replace("·", ",")
    text = re.sub(r"\s+", " ", text).strip(" ,")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text)
    text = re.sub(
        r"\b([A-Za-z]{2})\s+(\d{5}(?:-\d{4})?)\b",
        lambda match: f"{match.group(1).upper()} {match.group(2)}",
        text,
    )
    return text


def normalize_resort(raw: str) -> str:
    text = _clean_text(raw)
    text = re.sub(r"\s+", " ", text).strip(" ,;|-")
    if not text:
        return ""
    letters = [char for char in text if char.isalpha()]
    if letters and all(char.isupper() for char in letters):
        words = []
        for index, word in enumerate(text.split()):
            lower = word.lower()
            if index > 0 and lower in _SMALL_WORDS:
                words.append(lower)
            else:
                words.append(lower.capitalize())
        text = " ".join(words)
    return text


def _clean_text(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = text.replace("\xa0", " ")
    return text.strip()
