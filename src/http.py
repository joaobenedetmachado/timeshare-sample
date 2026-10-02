import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from src.log import fallback, success

RETRY_STATUSES = {429, 500, 502, 503, 504}


class HttpClient:
    """Polite HTTP client: robots.txt, a shared delay, and limited retries."""

    def __init__(
        self,
        user_agent: str,
        delay_seconds: float = 2.0,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self._last_request_at = 0.0
        self._robots: dict[str, RobotFileParser | None] = {}
        self._client = httpx.Client(
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=timeout_seconds,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def get_text(self, url: str, *, quiet: bool = False) -> str | None:
        if not self.allowed(url):
            if not quiet:
                fallback(_label(url), "pular (robots.txt)")
            return None

        for attempt in range(1, self.max_retries + 1):
            self._wait()
            try:
                response = self._client.get(url)
            except httpx.HTTPError:
                if attempt == self.max_retries:
                    if not quiet:
                        fallback(_label(url), "seguir sem essa página")
                    return None
                fallback(_label(url), "de novo")
                time.sleep(min(8.0, 2 ** (attempt - 1)))
                continue

            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                fallback(_label(url), "de novo")
                time.sleep(min(8.0, 2 ** (attempt - 1)))
                continue

            if response.status_code >= 400:
                if not quiet:
                    fallback(_label(url), "seguir sem essa página")
                return None

            return response.text

        return None

    def allowed(self, url: str) -> bool:
        parser = self._robot_parser(url)
        if parser is None:
            return False
        return parser.can_fetch(self.user_agent, url)

    def _robot_parser(self, url: str) -> RobotFileParser | None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin in self._robots:
            return self._robots[origin]

        robots_url = f"{origin}/robots.txt"
        self._wait()
        try:
            response = self._client.get(robots_url)
        except httpx.HTTPError:
            fallback(parsed.netloc, "pular o site")
            self._robots[origin] = None
            return None

        parser = RobotFileParser()
        parser.set_url(robots_url)
        if response.status_code == 404:
            fallback(f"{parsed.netloc}/robots.txt", "ler as páginas públicas")
            parser.parse([])
        elif response.status_code >= 400:
            fallback(parsed.netloc, "pular o site")
            self._robots[origin] = None
            return None
        else:
            parser.parse(response.text.splitlines())

        crawl_delay = parser.crawl_delay(self.user_agent) or parser.crawl_delay("*")
        if crawl_delay and crawl_delay > self.delay_seconds:
            success(f"{parsed.netloc} espera {crawl_delay:g}s")
            self.delay_seconds = float(crawl_delay)

        self._robots[origin] = parser
        return parser

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.delay_seconds - elapsed
        if self._last_request_at and remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()


def _label(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if len(path) > 48:
        path = path[:45] + "..."
    return f"{parsed.netloc}{path}"
