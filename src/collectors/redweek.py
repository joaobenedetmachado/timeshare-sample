import logging

from bs4 import BeautifulSoup

from src.http import HttpClient
from src.models import Record

logger = logging.getLogger(__name__)

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
        html = self.http.get_text(SAMPLE_URL)
        if not html:
            logger.info("RedWeek page unavailable; no records emitted")
            return []

        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select("header, footer, nav"):
            node.decompose()
        phones = [anchor.get_text(" ", strip=True) for anchor in soup.select("a[href^='tel:']")]
        if not phones:
            logger.info(
                "RedWeek public page %s has no listing telephone. "
                "Owner contact is membership-gated, so no record was emitted.",
                SAMPLE_URL,
            )
            return []

        logger.info("RedWeek exposed %s telephone link(s); leaving them uncollected without a named contact block", len(phones))
        return []
