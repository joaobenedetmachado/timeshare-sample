# Data quality

File: `output/timeshare_owners.csv`, parsed on 2 October 2026 (`2026-10-02T19:04:52Z` to `2026-10-02T19:07:07Z`).

20 rows. Every column is filled. Deduplication removed 1 row: two SellMyTimeshareNow listings named the same resort, on the same marketplace phone, and collapsed to the fuller row. The same phone is kept when the person or the resort is different.

| Field | Filled |
| --- | ---: |
| name, phone, address, resort, source URL, contact type | 20 of 20 |

Contact type: 3 `agent`, 17 `company`, 0 `owner`.

| Source | Collected | In the CSV | Left out |
| --- | ---: | ---: | --- |
| LTRBA | 20 | 3 | 17 profiles named a brand or a program instead of one property, or the place was not specific. Five other cards had no resort and no place, so they were not collected. |
| SellMyTimeshareNow | 8 | 5 | 2 locations were not a street. 1 repeated resort was removed in deduplication. |
| Pinnacle Vacations | 12 | 12 | Stopped at the cap of 12 distinct resorts. Not a quality drop. |
| RedWeek | 0 | 0 | The public company page has no listing phone. |

The 12 Pinnacle rows share `+18004855632` and the Fort Myers office. Each row is a different resort. The 5 SellMyTimeshareNow rows share `+18552993829`, the marketplace line, and each row is a different listing.

The 3 LTRBA rows are brokers, not owners. Alexis Nunez, Betty Zipf, and Mario Collura are in Oceanside, CA, for Four Seasons Residence Clubs at Aviara, on the shared office line `+13108237552`.

Dropped at validation because the resort was a brand, a program, or a list, not one property: Adriana Prata, Alanna Hatz, Carl Thoms, Caryn Cook, David Cortese, Jan Nichols, Jessica ODaniel, John Raymond, Karl Brodersen, Kelly Marshall, Mark Bell, Nancy Snyder, Shelley Preece, Teresa Denney, and William (Bill) Stephan. `Marriott Destination Points` and `Breckenridge Resorts` are in that group. Julie Bett and Bill Gabrielli were dropped because the address was not a specific place.

`owner` is unused. No sampled page prints an owner's name and that person's phone. A "for sale by owner" badge is a listing label, and it does not change `contact_type`.

Checked with `python -m unittest discover -s tests -v`. Those tests do not hit the network. They cover phone formatting, a brand list being rejected, a state-only address being rejected, and the same phone kept when the resort differs.
