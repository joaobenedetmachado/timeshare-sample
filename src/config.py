import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs without overriding variables already set."""
    env_path = path or Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return float(raw)


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    request_delay_seconds: float
    max_retries: int
    request_timeout_seconds: float
    user_agent: str
    output_path: Path
    smtn_max_listings: int
    pinnacle_max_resorts: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            request_delay_seconds=_float("REQUEST_DELAY_SECONDS", 2.0),
            max_retries=_int("MAX_RETRIES", 3),
            request_timeout_seconds=_float("REQUEST_TIMEOUT_SECONDS", 30.0),
            user_agent=os.environ.get(
                "USER_AGENT",
                "TimeshareDataSample/1.0 (public pages only; educational sample)",
            ),
            output_path=Path(os.environ.get("OUTPUT_PATH", "output/timeshare_owners.csv")),
            smtn_max_listings=_int("SMTN_MAX_LISTINGS", 8),
            pinnacle_max_resorts=_int("PINNACLE_MAX_RESORTS", 12),
        )
