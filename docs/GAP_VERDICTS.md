# SeriAll gap verdicts (Phase 2b)

Definitive "no file" / "held style" verdicts. A gap here means the data was
examined and honestly cannot be encoded — never a skipped brand. Each entry
states the exact reason and what, if anything, could unblock it.

## Brands with no file (Phase 2b)

### Mitsubishi — definitive gap, no file
Page: https://www.building-center.org/mitsubishi-hvac-age/
The year is a single fiscal-year digit and the page states the decade
"must be assumed" (from nearest ANSI code date or unit condition — external
context a serial-only decoder does not have). The "2008 or 2018" pair is
attached to two sample serials starting in digit 8, not a general rule,
and says nothing about digits 0–7 or 9. No page-stated model era,
production range, style start/end date, or decade table exists. Month
(1–9, X/Y/Z) is documented but cannot rescue the year, and the fiscal
April–March shift means Jan–Mar units carry the previous fiscal-year code.
Unblockers, in order: (1) Mitsubishi-official or authoritative
documentation bounding a style or model series to a production era;
(2) a published digit→decade table per model series. Absent those, the
page's own instruction stands: contact the manufacturer.

### Fujitsu — definitive no-file
Page: https://www.building-center.org/fujitsu-hvac-age/
The page states the manufacture date cannot be determined: Fujitsu tech
services could only place a unit vaguely in the mid-1990s, serials are
sequential with no date coded in them, and a suspicion that the year may
be encoded in serial letter prefixes is explicitly unconfirmed (no
pattern determined, unknown whether letters are skipped). The
unconfirmed suspicion must not be encoded. Dating routes the page gives
(contact Fujitsu Service at (866) 952-8324 with the serial, or the
online warranty lookup for a registered unit) are lookups, not serial
rules, and create no file.

### Burnham — definitive no-file
Page: https://www.building-center.org/burnham-hvac-age/
There is no serial-number decoding rule on the page. Model, serial, and
manufacturing date sit on a silver label inside the panel; the date
itself is printed in MM/YYYY format (documented example: serial
64157594, printed date 10/1999). Without a dated tag, the manufacturer
must be contacted with model and serial. A 2017 reader update redirects
residential-boiler inquiries to USA Boiler (888-432-8887 ext. 8400) and
a 2019 reader update links a US Boiler repair-parts lookup tool — both
are lookup routes, not decodable systems, and create no file.

## Brands with a file but held styles (Phase 2b)

### LG Style 1 — held (decade-ambiguous, no bound)
File: `data/brands/lg.json` (Style 2 shipped; Style 1 held).
Year is a single digit with no page-stated decade bound. Digit 4 is
documented as 2004 (diagram sample), 2014 and 2024 (page text + plate
photo); digit 2 as 2012 (plate photo). A two-candidate [2014, 2024]
table for digit 4 is therefore disproven, and an assumed 2000–2026
multi-candidate bound was rejected as assumed, not page-stated.
Unresolved diagram anomaly, not encoded: the Style 1 diagram claims
1201KAPB00104 = January 2012 under a 4-character date code,
contradicting the current rule (position 1 = year digit, 2–3 = month);
such serials correctly fail under the current rule. Unblocker: a
page-stated era bound or manufacturer decade table.

### Carrier older systems — held
File: `data/brands/carrier.json` (modern WWYY shipped).
1960s single-digit year and 1970s letter+digit systems appear only in a
single inspector-training source, incomplete. Held pending a second
source or manufacturer documentation.

### Amana authority-tier caveat (file shipped, reversible)
File: `data/brands/amana.json`.
Styles come from Amana-specific third-party decoders (PickHVAC primary,
corroborated by GGR, HowToLookAtAHouse, InterNACHI), not manufacturer
documentation. If the bar is manufacturer/official only, delete this
file and record Amana as a gap — one move, no other file affected.

### Other held styles (image reads still open)
Text fetch cannot OCR chart images, so these remain held pending a
live-browser image read (full URL list in the Phase 2b report):
RESOLVED BY THE IMAGE PASS (Nov 8) -- now shipped: Goodman Style 2 (PTAC letter tables); Daikin styles 3, 4, 5, 6, 8, 9 (style 5's Daikin-vs-McQuay description conflict resolved in favor of the chart: 3rd character is month, not week); Tempstar styles 4-6; Keeprite styles 4-5; Coleman style 1; Luxaire style 1 (the K-month conflict is real, chart-vs-chart: Luxaire K=October vs York/Coleman K=September, and each brand file follows its own chart) and style 5 (its tables are identical to style 4's, as the chart itself shows); Trane page styles 4-7 (style 4's first-vs-last position ambiguity resolved by shipping two styles; style 6's L/M/N table is in the chart); Reznor style-1 1975-1994 (chart-sourced, not backward arithmetic); York parenthetical-prefix serials (e.g. (S)EBHM062202 -- shipped as a literal-parenthesis pattern under a coordinator ruling, since the locked normalization strips spaces/dashes only and the parentheses survive). Payne styles 3-4 are now Payne-page-confirmed (their charts match the Bryant-transcribed tables exactly). WaterFurnace month (January, chart-confirmed) and AllStyle Style 1 (year-only, reversed-split) also shipped in the image pass; Water Heater Index is a separate v2 program, not started.
STILL HELD: Daikin style 1 (label-only, not encodable); Payne style 5 (pre-1970 -- the chart was read and contains NO digit-to-year mapping; the year comes from an unpublished sequence-number lookup); Trane page Style 8 (European; page states it cannot be decoded); Reznor style-1 1949-1974 single-letter codes (chart-verified but no real example serial exists); Bosch Styles 2-3 (page states the year cannot be determined); Weil-McLain 6-digit CP numbers (early-1980s and prior, contact manufacturer); Zoneline (year codes unbounded 1944-2013, no zoneline.json).
