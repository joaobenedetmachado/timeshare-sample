# Data quality

File: `output/timeshare_owners.csv`, parsed on 2 October 2026 (`2026-10-02T19:04:52Z` to `2026-10-02T19:07:07Z`).

20 rows. Every column is filled. Deduplication removed nothing: each phone, name, and resort combination is unique. The same phone repeats only when the person or the resort is different.

| Field | Filled |
| --- | ---: |
| name, phone, address, resort, source URL, contact type | 20 of 20 |

Contact type: 3 `agent`, 17 `company`, 0 `owner`.

| Source | Rows | What the row is |
| --- | ---: | --- |
| LTRBA | 3 | Alexis Nunez, Betty Zipf, and Mario Collura. Same Oceanside office line, one club: Four Seasons Residence Clubs at Aviara. |
| SellMyTimeshareNow | 5 | Marketplace phone `+18552993829`. Each row is a different resort and a street from the listing. |
| Pinnacle Vacations | 12 | Brokerage phone `+18004855632` and the Fort Myers office. Each row is a different resort. The cap is 12. |
| RedWeek | 0 | The public company page has no listing phone. |

Profiles that only named a brand or a points program, and listings whose location was not a street, are not in the file.

Checked with `python -m unittest discover -s tests -v`. Those tests do not hit the network.
