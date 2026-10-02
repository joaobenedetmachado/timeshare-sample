import logging

from src.pipeline import run

__all__ = ["run"]


def main() -> None:
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    run()


if __name__ == "__main__":
    main()
