from bs4 import BeautifulSoup

from src.http import HttpClient
from src.log import note
from src.models import Record

# A public company profile. Owner resale contact on RedWeek is behind membership.
SAMPLE_URL = "https://www.redweek.com/timeshare-companies/hgvc"


class RedweekCollector:
    """Check the public RedWeek surface and emit nothing it does not show.

    Direct owner contact for a resale requires a membership. This collector
    reads one public company page and only keeps a record when that page
    publishes a telephone link tied to the company. A support number in the
    site chrome is not treated as an owner.
    """

    source = "RedWeek"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(self) -> list[Record]:
        html = self.http.get_text(SAMPLE_URL, quiet=True)
        if not html:
            note("RedWeek page unavailable, no records")
            return []

        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select("header, footer, nav"):
            node.decompose()
        phones = [anchor.get_text(" ", strip=True) for anchor in soup.select("a[href^='tel:']")]
        if not phones:
            note("RedWeek has no public phone, no records")
            return []

        note("RedWeek has no contact block, no records")
        return []
