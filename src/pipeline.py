"""collect → normalize → validate → deduplicate → export."""

from src.collectors import LtrbaCollector, PinnacleCollector, RedweekCollector, SmtnCollector
from src.config import Settings
from src.deduplicate import deduplicate
from src.export import export_csv
from src.http import HttpClient
from src.log import fallback, success
from src.models import Record
from src.validate import normalize_record, validate


def run(settings: Settings | None = None) -> list[Record]:
    settings = settings or Settings.from_env()
    raw = _collect(settings)
    normalized = [normalize_record(record) for record in raw]
    success(f"normalize  {len(normalized)} records")
    valid = validate(normalized)
    success(f"validate  {len(valid)} records")
    unique = deduplicate(valid)
    removed = len(valid) - len(unique)
    if removed:
        fallback(f"{removed} duplicates", "keeping the fuller row")
    success(f"dedupe  {len(unique)} records")
    export_csv(unique, settings.output_path)
    success(f"csv  {len(unique)} rows in {settings.output_path}")
    return unique


def _collect(settings: Settings) -> list[Record]:
    http = HttpClient(
        user_agent=settings.user_agent,
        delay_seconds=settings.request_delay_seconds,
        max_retries=settings.max_retries,
        timeout_seconds=settings.request_timeout_seconds,
    )
    collectors = [
        LtrbaCollector(http),
        SmtnCollector(http, max_listings=settings.smtn_max_listings),
        PinnacleCollector(http, max_resorts=settings.pinnacle_max_resorts),
        RedweekCollector(http),
    ]
    raw: list[Record] = []
    try:
        for collector in collectors:
            try:
                found = collector.collect()
            except Exception as exc:
                fallback(str(collector.source), f"the next source ({exc.__class__.__name__})")
                continue
            if found:
                success(f"{collector.source}  {len(found)} records")
            raw.extend(found)
    finally:
        http.close()
    return raw
