# Methodology

This sample collects a small set of public timeshare contacts and listing resorts, then cleans them with an explicit pipeline:

```
Sources
  ↓
Collectors
  ↓
Raw records
  ↓
Normalization
  ↓
Validation
  ↓
Deduplication
  ↓
CSV output
```

The goal is a verifiable sample, not a large scrape. When a field is not on the page, it stays empty.

## Source discovery

Four public sites were reviewed:

| Source | What is public | What was kept |
| --- | --- | --- |
| [LTRBA member directory](https://www.licensedtimeshareresalebrokers.org/members-all) | Named licensed brokers and a phone on each card. Street address and a single resort are not structured fields. | One row per member. `contact_type=agent`. `resort` and `address` stay empty. |
| [SellMyTimeshareNow listings](https://www.sellmytimesharenow.com/timeshares-for-sale/) | Resort name, ad number, and a marketplace "call now" number on the detail page. | One row per detail page, capped. The phone is the marketplace line, so `contact_type=company`. |
| [Pinnacle Vacations state results](https://www.pinnaclevacations.com/state-search.aspx) | Resort name on each result, plus the brokerage office phone and address in the page footer. | One row per distinct resort, capped. `contact_type=company`. |
| [RedWeek](https://www.redweek.com/timeshare-companies/hgvc) | Company descriptions. Direct owner contact for a resale requires membership. | No rows. A telephone that is not on the page is not invented. |

`robots.txt` is read before any page on that host. A missing file (HTTP 404) is treated as allowed. If `robots.txt` cannot be fetched, that host is skipped. Paths disallowed for the sample user agent are not requested. SellMyTimeshareNow publishes `Crawl-delay: 2` for `User-agent: *`; the client uses the larger of that value and `REQUEST_DELAY_SECONDS`.

The sample does not log in, solve CAPTCHAs, use a residential proxy, or send a browser-impersonation user agent.

## Collection

`src/http.py` is shared by every collector:

- one identifiable `User-Agent`
- a delay between requests
- retries with backoff for network errors and HTTP 429/5xx
- no retry for HTTP 403, 404, or other client errors

Each collector returns `Record` objects. A collector that fails is logged and does not stop the others.

### LTRBA

The directory card is the source for the broker's name, phone, and the resorts or brands they name. When the card states a city, state, or office, that place is the address. When it does not, the pipeline reads the office address from the company site on the same card (the email domain) and keeps it only when that page prints a street or a city. A broker is left out of the CSV when the public text still has no resort and no place. Four cards in this run were in that group.

### SellMyTimeshareNow

The index page supplies detail URLs. Each detail page supplies the resort from the document title. The phone is read from `span.phone-number` inside the listing, not from the site-wide header. The resort street address on the page is the property location, so it is not copied into `address`. The badge "for sale by owner" describes the listing type. It is not a person's name, and it does not set `contact_type` to `owner`.

### Pinnacle Vacations

Results are read from a few state search pages (Florida, Hawaii, Nevada, South Carolina) until the resort cap is reached. Repeated resorts on the same page collapse to one row before export as well. The toll-free number and the Fort Myers office address are parsed from that same results page. They are the brokerage contact shown with the listing, not the owner.

### RedWeek

One public company page is fetched. After `header`, `footer`, and `nav` are removed, the parser looks for `tel:` links. The sampled page has none. Owner phone, owner name, and owner address are not filled in from anywhere else.

## Normalization

Applied in `src/normalize.py` after collection:

- **Phone.** Digits are kept and formatted as E.164 (`+1` plus 10 digits for NANP numbers). A leading UK trunk `0` after `+44` is removed. An extension such as `x4` is preserved. If several numbers are joined with " or ", only the first is kept. Anything that is not an unambiguous number becomes an empty string.
- **Name.** HTML entities are decoded and whitespace is collapsed. A value longer than 80 characters is dropped so a biography cannot land in the name column.
- **Address.** Bullets become commas, comma spacing is normalized, and the state abbreviation before a ZIP code is uppercased. No geocoding and no guessed suite or city.
- **Resort.** An all-caps resort name is title-cased, with small words (`and`, `at`, `of`, `the`, `on`) left lowercase after the first word. Mixed-case names are left as published.

## Validation

A row is dropped only when it cannot be checked or contains nothing useful:

- `contact_type` must be `owner`, `agent`, `company`, or `unknown`
- `source_url` must be an `http` or `https` URL
- `collected_at` must be present
- a non-empty phone must already be in normalized form
- at least one of `name`, `phone_number`, or `resort` must be present

Empty address or empty resort is allowed.

## Deduplication

The key is normalized phone (extension ignored) + name + resort, compared case-insensitively.

- The same person at the same resort is one row. The copy with more filled fields is kept.
- The same office line at two different resorts stays as two rows, because the resort is different.
- Two agents who share an office line stay as two rows, because the name is different.

## Export

`output/timeshare_owners.csv` is UTF-8, with a header and this column order:

`name`, `phone_number`, `address`, `resort`, `source`, `source_url`, `collected_at`, `contact_type`

Rows are sorted by source, name, and resort so repeated runs are easy to diff when the upstream pages have not changed. `collected_at` is the UTC time the page was parsed.

## Contact classification

| Value | Rule used here |
| --- | --- |
| `agent` | A named person on the LTRBA licensed-broker directory. |
| `company` | The phone on the page is the marketplace or brokerage line, and the page names that business. |
| `owner` | Not used. None of the sampled pages identify a natural person as the owner and publish that person's phone. |
| `unknown` | Used when a collector cannot tell who a phone belongs to. The RedWeek check produced no row rather than an unknown placeholder. |

## Tooling note: Scrapit

[scrapit](https://github.com/joaobenedetmachado/scrapit) is a YAML-driven scraper with fetch, transform, and storage built in. It was not used as a dependency, for four reasons:

1. The point of this sample is the quality pipeline. Phone, address, contact type, and cross-source deduplication are domain rules, and they are easier to review in the Python modules than inside generic YAML transforms.
2. The pages that actually contain contacts are not one shared HTML shape. LTRBA is a Wix repeater, Pinnacle is an old ASP.NET results table, and SellMyTimeshareNow separates the listing phone from the site header.
3. Scrapit also ships stealth, proxy, and Bright Data backends for bot-protected sites. Those features conflict with the rule that this sample must not bypass access controls.
4. The package is still early. Pinning it would make the sample harder to install than `httpx` and `BeautifulSoup`.

Scrapit would fit later as an optional fetch adapter for stable, selector-friendly pages, behind the same `Record` type, using only the BeautifulSoup backend.

## What this sample refuses to do

- Copy a site-wide support number onto a listing and call the person an owner.
- Treat a resort street address as the contact's home or office address unless the page presents it as the contact address. Pinnacle's footer is the brokerage office, so that address is kept and labeled `company`. The resort street on a SellMyTimeshareNow detail page is not.
- Infer a resort from a broker biography. Specialties such as "Marriott" or "Hilton" are brands, not one resort.
- Fill a blank by searching another site for the same person.
