# Timeshare contacts

[![Tests](https://github.com/joaobenedetmachado/timeshare-sample/actions/workflows/tests.yml/badge.svg)](https://github.com/joaobenedetmachado/timeshare-sample/actions/workflows/tests.yml)

Public timeshare pages, cleaned into one CSV. A row is kept only when the page prints a name, a phone, a place, and one resort. The URL for that page is on the row.

The file is `output/timeshare_owners.csv`. Counts for this run are in [docs/data-quality.md](docs/data-quality.md). The field rules are in [docs/methodology.md](docs/methodology.md).

## Columns

| Column | What it is |
| --- | --- |
| `name` | Person or business printed on the page. |
| `phone_number` | That contact's phone, in E.164. |
| `address` | A street, or a city and region. A state by itself is not kept. |
| `resort` | One property. A list of brands is not kept. |
| `source` | Site the row came from. |
| `source_url` | Public page where the row can be checked. |
| `collected_at` | UTC time that page was parsed. |
| `contact_type` | `agent`, `company`, `owner`, or `unknown`. |

`agent` is a named broker on the LTRBA directory. `company` is a marketplace or brokerage line. `owner` is unused: none of these public pages print an owner's name and that person's phone.

This file has 20 rows.

| Source | Rows | Note |
| --- | ---: | --- |
| LTRBA | 3 | Alexis Nunez, Betty Zipf, and Mario Collura in Oceanside, CA, for Four Seasons Residence Clubs at Aviara. |
| SellMyTimeshareNow | 5 | Marketplace phone. One resort and a street on each row. |
| Pinnacle Vacations | 12 | One Fort Myers office phone. A different resort on each row. |
| RedWeek | 0 | No listing phone on the public page. |

## Pipeline

```mermaid
flowchart LR
    Sources --> Collectors --> Normalize --> Validate --> Deduplicate --> CSV
```

`src/pipeline.py` runs the stages in that order. Each site is one file in `src/collectors/`. Normalize, validate, deduplicate, and export are the stages next to it. HTTP, settings, and the record type sit in the same folder.

```
timeshare-sample/
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   ├── methodology.md
│   ├── data-quality.md
│   └── using-ai.md
├── src/
│   ├── main.py
│   ├── pipeline.py
│   ├── collectors/
│   ├── normalize.py
│   ├── validate.py
│   ├── deduplicate.py
│   └── export.py
├── tests/
│   ├── test_normalize.py
│   └── test_deduplicate.py
└── output/
    └── timeshare_owners.csv
```

## How to run

Python 3.11 or newer.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

macOS or Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Optional settings are in `.env.example` (`REQUEST_DELAY_SECONDS`, listing caps, output path). Copy it to `.env` to override the defaults. The default delay is already 2 seconds.

The transformation rules can be checked without the network:

```bash
python -m unittest discover -s tests -v
```

A new run fetches the pages again and rewrites the CSV. `collected_at` changes. Listings change too, so the file is the sample from the time it was generated.

## What is not in this file

RedWeek, SellMyTimeshareNow, and Pinnacle do not publish the owner's name and phone on the open page. RedWeek puts that behind an account. SellMyTimeshareNow and Pinnacle publish the resort and a company number. LTRBA publishes licensed brokers. Those rows are labeled `agent` or `company`.

A biography that only lists brands, an address that is only a state, and a location that says "Multi-Destination" are left out. Filling them in would make the CSV look fuller and make it wrong.

## Why a browser would not change this file

The fetch is an HTTP GET. BeautifulSoup and a few regular expressions read the HTML that comes back. City, phone, resort, and the listing address on these four sites are already in that HTML. They are not drawn later by JavaScript.

Selenium or Playwright would load the same public pages in a browser. That can click a "next page" control and collect more brokers or more listings. The new rows would still be an LTRBA agent or the same company phone. RedWeek's owner contact stays behind an account. A browser does not cross that without a login, and this sample does not log in.

## Possible next steps

- Page through Pinnacle and SellMyTimeshareNow past the current caps. That adds resorts, not owners. The phone on those rows stays the office or the marketplace line.
- Treat near-duplicate resort titles on one page as one place. Pinnacle prints Oasis Lakes, The Fountains, and Lake Eve as separate headings for one Orlando complex.
- Add another public source only when the page itself prints a person's name and that person's phone. Label the row `owner` then. Until that page exists, `owner` stays unused.

How the work was split, including what was handed to an AI assistant, is in [docs/using-ai.md](docs/using-ai.md).
