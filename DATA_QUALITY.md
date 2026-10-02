# Data quality report

Run written to `output/timeshare_owners.csv` on 2 October 2026 (`collected_at` from `2026-10-02T18:28:25Z` to `2026-10-02T18:29:57Z`).

The export has **41 rows**. Every column is filled. Deduplication removed **0** rows: all 41 keys (phone digits, ignoring the extension, plus name plus resort) are unique. Shared phone numbers were kept when the person or the resort was different.

Nothing in this file was inferred. A missing resort or place removes the row. It does not become an empty cell.

## Coverage

| Field | Filled | Empty |
| --- | ---: | ---: |
| `name` | 41 | 0 |
| `phone_number` | 41 | 0 |
| `address` | 41 | 0 |
| `resort` | 41 | 0 |
| `source_url` | 41 | 0 |
| `contact_type` | 41 | 0 |

`contact_type` in this file: 21 `agent`, 20 `company`, 0 `owner`, 0 `unknown`.

`owner` is unused on purpose. A "for sale by owner" label names the listing type, not a person, and it does not publish that person's phone.

20 distinct phone numbers. Repeats that are not duplicates:

| Phone | Rows | Why it stays |
| --- | ---: | --- |
| `+18004855632` | 12 | Pinnacle brokerage line, one row per resort |
| `+18552993829` | 8 | SellMyTimeshareNow marketplace line, one row per listing |
| `+13108237552` | 3 | Three named LTRBA brokers |
| `+14356496461` | 2 | Two named LTRBA brokers |

## Sources

| Source | Raw | Valid | Rejected | Notes |
| --- | ---: | ---: | ---: | --- |
| LTRBA | 25 | 21 | 4 | Licensed brokers. `contact_type=agent`. |
| SellMyTimeshareNow | 8 | 8 | 0 | Stopped at the listing cap (`SMTN_MAX_LISTINGS=8`). Marketplace phone, so `company`. |
| Pinnacle Vacations | 12 | 12 | 0 | Stopped at the distinct-resort cap (`PINNACLE_MAX_RESORTS=12`). Office phone and Fort Myers address, so `company`. |
| RedWeek | 0 | 0 | 0 | Public company page was fetched. No listing phone, so no row was created. |

Raw is what the collector was willing to turn into a record before the export rule. The SellMyTimeshareNow and Pinnacle caps are collection limits, not rejected rows. The index and the state pages contain more listings than the caps. Those extra pages were not fetched.

### LTRBA, the four left out

A card is exported only when both a resort and a place are on the card or on the company site named by that card. These four were not:

| Name | Why |
| --- | --- |
| Syed Sarmad | No clean resort after the card and the company page were read. |
| Kenji Iwasa | Biography did not name a resort and a place. |
| Steven Ramey | Company host did not resolve, so the missing place could not be filled. |
| Joseph Takacs | Company host was skipped because `robots.txt` could not be read. |

### RedWeek

`https://www.redweek.com/timeshare-companies/hgvc` is public. After the header, footer, and navigation are removed, the page has no `tel:` link tied to a listing. Owner name, phone, and address for a resale sit behind membership. No support number was copied in to fill the gap.

## What validation drops

A record reaches the CSV only when all of these hold:

- `contact_type` is `owner`, `agent`, `company`, or `unknown`
- `source_url` is `http` or `https`
- `collected_at` is set
- `phone_number` is E.164, optional extension (`+19704531226 x4`)
- `name`, `address`, and `resort` are all non-empty

In this run the four LTRBA cards were dropped in the collector, before validation. Validation itself had nothing left to reject.

## Checks

`python -m unittest discover -s tests -v` covers phone normalization (NANP, UK trunk zero, extension, "or" keeping the first number), resort title case, address bullets, deduplication of the same contact at the same resort, and keeping the same phone at a different resort. It does not hit the network.
