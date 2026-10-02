# How I used AI on this sample

The brief asked for a list of timeshare owners with a name, a phone number, an address, and a resort, and it named RedWeek, SellMyTimeshareNow, and Pinnacle as examples. Before any code, I opened those pages and wrote down what a person can see without an account. The resort is often public. The owner's phone is not. RedWeek puts it behind membership. The other two publish a company number. That was the split that mattered: collect only what the page prints, and do not invent the rest to match the word "owner".

I then broke the work into pieces I could check one at a time: one collector per site, then normalize, validate, deduplicate, and export. Parsing a page and drafting the tests are the parts I delegated to an AI assistant. I read the result against a real page. A rule that filled a blank street, or that labeled a broker as an owner, was rejected. I can hand over a parser or a test. I do not hand over the decision of what a row is allowed to mean, because that is the part a bad guess would hide.

What scales is that shape. A new public site is another collector that returns the same record, and the checks on the phone, the place, and a single resort stay where they are. What does not scale is the page. Each site puts the contact in a different spot, and a login wall stays a login wall no matter who generated the scraper.
