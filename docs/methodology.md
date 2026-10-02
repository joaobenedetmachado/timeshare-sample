# Methodology

Four public sites, one record shape, then the same checks for every row. A value that is not on the page is left out. It is not guessed.

## What each site actually shows

[LTRBA](https://www.licensedtimeshareresalebrokers.org/members-all) is a directory of licensed resale brokers. The card has a name and a phone. The profile form has a city, and sometimes a biography or a brand list. That person is an `agent`. They are not recorded as the owner.

[SellMyTimeshareNow](https://www.sellmytimesharenow.com/timeshares-for-sale/) listing pages name one resort, print a location, and show a call-now number. That number is the marketplace line, so the row is `company`. The "for sale by owner" badge is a listing label. It is not a person's name and it does not change the contact type.

[Pinnacle Vacations](https://www.pinnaclevacations.com/state-search.aspx) state results name the resort on the card. The phone and the street in the footer are the brokerage office in Fort Myers. Same company on every row, different resort. `contact_type` is `company`.

[RedWeek](https://www.redweek.com/timeshare-companies/hgvc) was checked because it was named in the brief. The public company page has no listing phone once the header, footer, and navigation are removed. Owner contact for a resale requires an account. No row is created to fill that gap.

## Collection

`src/http.py` is the only client. It reads `robots.txt` first. A 404 means the host has no file, so public pages are allowed. Any other failure skips that host. SellMyTimeshareNow asks for a 2 second crawl delay, and the client waits at least that long. Retries are for network errors and HTTP 429 or 5xx. A 403 or 404 is not retried.

One collector per site, each returning `Record` objects. If a collector throws, the run logs one line and moves to the next site.

LTRBA reads the directory, then each member profile. The address is the city and state on the profile. If that is empty, the company site on the card is tried. The resort is kept only when the profile names one property. A list of brands is not stored as the resort.

SellMyTimeshareNow takes resort names from the page title and the location from `div.location`. A location that only says "Outside US" or "Multi-Destination" is not an address. The phone comes from `span.phone-number` on the listing, not from the site header.

Pinnacle reads Florida, Hawaii, Nevada, and South Carolina until it has 12 distinct resorts. The toll-free number and the office street are parsed from that same results page.

## Cleaning

Normalization lives in `src/normalize.py`.

Phones become E.164. A US number is `+1` and ten digits. A UK trunk `0` after `+44` is removed. An extension stays (`+19704531226 x4`). When two numbers are joined with "or", only the first is kept. A fragment is cleared.

Names longer than 80 characters are cleared, so a biography cannot land in the name column. Addresses lose bullet characters and extra commas. The state before a ZIP is uppercased. Nothing is geocoded.

An all-caps resort is title-cased. Mixed-case names stay as published.

## What gets into the CSV

Validation drops a row unless all of this is true:

- `contact_type` is `owner`, `agent`, `company`, or `unknown`
- `source_url` is an `http` or `https` link
- `collected_at` is set
- the phone is E.164, with an optional extension
- the address is a street, or a city plus a region, not a state by itself and not a list of markets
- the resort is one property name, not a brand list and not the word "Multi-Destination"

Deduplication key: phone digits (extension ignored), name, and resort. The same person at the same resort collapses to the fuller row. The same office line at two resorts stays. Two brokers on one phone stay.

Export is a UTF-8 CSV at `output/timeshare_owners.csv`, sorted by source, name, and resort. Counts for the current file are in [data-quality.md](data-quality.md).

## Contact type

| Value | When it is used |
| --- | --- |
| `agent` | A named person on the LTRBA directory. |
| `company` | The phone belongs to the marketplace or the brokerage, and the page names that business. |
| `owner` | Not used. No sampled page prints an owner's name and that person's phone. |
| `unknown` | Reserved for a phone whose side cannot be told. This run did not need it. |
