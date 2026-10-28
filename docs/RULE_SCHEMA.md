# SeriAll rule schema (locked for Phase 2 curation; extended in Phase 2b)

Phase 2b additions (backward-compatible — all Phase 2 files still validate
unchanged): split positions, dual-candidate year tables, `codeTable`,
`rangeTable`, and string-keyed tables. See the sections marked "Phase 2b".

One file per brand in `data/brands/<slug>.json`. Files whose names start with
`_` (e.g. `_example.json`) are schema examples and are **never** built into
the index.

Format choice: **JSON**, not YAML. The whole chain is JSON — rule file →
built index → app fetch — so there is no YAML parser dependency anywhere,
and the app can consume the built index directly. Human-readable notes go in
`notes` fields, not in comments (JSON has none).

## Brand file

```json
{
  "brand": "Goodman",
  "slug": "goodman",
  "aliases": ["GmC"],
  "parent": "Daikin Group",
  "sisters": ["Amana", "Janitrol"],
  "sourceUrl": "https://www.building-center.org/goodman-hvac-age/",
  "notes": "Free-text curator notes. Never Building Center prose.",
  "usesStylesOf": null,
  "styles": [ "...see below..." ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `brand` | yes | Display name, as Building Center names it. |
| `slug` | yes | Lowercase, `&` → `and`, spaces → hyphens. Unique across files. |
| `aliases` | no | Other names techs type for this brand (e.g. `GmC`). Used for matching user input. |
| `parent` | no | Parent company, as a fact (e.g. `Daikin Group`). |
| `sisters` | no | Sister / related brands sharing this rule system, as facts. |
| `sourceUrl` | yes | The brand's Building Center page. Also the app's fallback link. **Exception (Phase 2b):** when the Building Center page carries no serial system (history-only), `sourceUrl` is the actual rule source (manufacturer documentation or a corroborated decoder), and the Building Center page URL is recorded in `notes`. |
| `notes` | no | Curator notes, caveats, era remarks. Never copied prose. |
| `usesStylesOf` | no | Slug of another brand whose styles this brand reuses verbatim (sister-brand reuse). When set, `styles` must be empty and the builder copies the referenced brand's styles at build time, tagged as inherited. Reuse is explicit and visible — never silent duplication. |
| `styles` | yes, unless `usesStylesOf` is set | Ordered list of serial styles (below). Tried in order. |

## Style

A style is one serial-number system a brand has used (brands change systems
over time, so most brands have more than one).

```json
{
  "id": "style-1",
  "era": "1990s–present, 10-digit numeric serials",
  "pattern": "^\\d{10}$",
  "year": { "kind": "digits", "positions": [0, 2] },
  "month": { "kind": "digits", "positions": [2, 4] },
  "week": null,
  "yearFloor": 1960,
  "examples": [
    { "serial": "9704811080", "expectedYear": 1997, "expectedMonth": 4 }
  ],
  "notes": ""
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable within the brand (`style-1`, `style-2`, …). |
| `era` | no | Human-readable applicability (decade, serial shape, plant, …). |
| `pattern` | yes | Regex over the **normalized** serial (see below). The style is only attempted when the pattern matches. |
| `year` | yes | How the manufacture year is extracted (below). |
| `month` | no | How the manufacture month is extracted, if the system encodes one. |
| `week` | no | How the manufacture week is extracted, if the system encodes one. |
| `yearFloor` | no | Earliest plausible manufacture year for this style (default 1960). Used by century disambiguation. |
| `examples` | yes, ≥ 1 | Worked examples. **Every example must decode to its expected values or the builder refuses the brand.** An example may carry `expectedWeek` (checked when present) and `expectedApproximate` (checked when present, for `rangeTable` styles). `expectedYear` may be a single year or a candidate list (dual-candidate styles — the full list must match, order-insensitive; claiming a single year for a dual-candidate code fails the build). |
| `notes` | no | Caveats (plant variations, exceptions, private-label notes). |

## Normalization (applied before any style is tried)

1. Uppercase the input.
2. Strip spaces, dashes, and other separators.
3. Nothing else is changed — no characters are guessed or repaired.

Matching and extraction always run against the normalized serial.

## Field extraction

`positions` are **0-based, half-open** ranges into the normalized serial:
`[0, 2]` means the first two characters. Curators should double-check this —
Building Center describes positions 1-based ("1st & 2nd"), so subtract one.

### Split positions (Phase 2b)

A field's `positions` may also be a **list of ranges**,
e.g. `[[0, 1], [4, 5]]`: the slices are concatenated **in the order
listed** and then interpreted as usual. This covers systems whose year
digits are split across non-contiguous positions (e.g. York-style systems
where the two year digits sit at different places in the serial). A single
range `[s, e]` is the one-range case of the same rule. Any field (year,
month, week) may use split positions.

### Year

- `{ "kind": "digits", "positions": [s, e] }` — the sliced digits are a
  two-digit year `YY`, resolved by the century rule below; or a four-digit
  year, used as-is (must still pass the plausibility check). Year `digits`
  must slice exactly 2 or 4 characters.
- `{ "kind": "letterTable", "positions": [s, e], "table": { "B": 1987, ... } }`
  — the sliced code maps through an explicit table to a full year.
  See "String-keyed tables" and "Dual-candidate year tables" below.
  This is the shape used by letter-year systems (e.g. Trane's year letters).
- `{ "kind": "rangeTable", "positions": [s, e], "bands": [...] }` (Phase 2b)
  — see "rangeTable" below.

### Month

- `{ "kind": "digits", "positions": [s, e] }` — sliced digits must be 1–12.
  (Month digits may be 1–2 characters; the 2-or-4 rule applies to year
  digits only.)
- `{ "kind": "letterTable", "positions": [s, e], "table": { "A": 1, ... } }` —
  explicit code → month-number map (1 = January). Systems that skip codes
  (e.g. Lennox month letters A–M minus I) are expressed by simply omitting
  those codes from the table.

### Week

- `{ "kind": "digits", "positions": [s, e] }` — sliced digits must be 1–53.
  (Week digits may be 1–2 characters.)

### String-keyed tables (Phase 2b — ratification)

Table keys are **uppercase strings**, not just single letters: single
letters (`"B"`), digits (`"5"`), or multi-character codes (`"BK"`, `"K7Q"`).
This ratifies what Phase 2 files already use (Bryant/Payne digit-keyed
tables, Trane's digit year table, Reznor's 2-character `BK` code) — no
existing file changes were needed. Keys must be non-empty and uppercase;
year-table values are full four-digit years (or candidate lists, below);
month-table values are 1–12.

### Dual-candidate year tables (Phase 2b)

Cyclic code systems (e.g. a 21-year letter cycle) reuse codes across eras,
so some codes map to **two** possible years. Such a table value is a list,
e.g. `{ "A": [2001, 2022] }`, and a decode of that code returns the full
candidate list — an explicit, honest result, **not** a guessed single year
and **not** a silent first-match. Codes mapping to exactly one year stay
exact. The result carries `ambiguous: true` exactly when the year is a
candidate list; the future app must present both years flagged ambiguous.
An example for a dual-candidate code must list the full candidate set
(order-insensitive); claiming a single year for such a code fails the
build. A code whose candidates cannot be bounded to a useful set (e.g. an
unbounded multi-decade list) is not encoded — that style stays a gap.

### Single-digit years (Phase 2b — policy)

A single-digit year code is **never** resolved by a computed decade rule
(the decade "must be assumed" problem). It may only be encoded as an
explicit digit-keyed table (above) where the source page bounds the era —
e.g. a model production range limiting a digit to one year, or to a
two-element candidate list. The bound must be cited in the style's `notes`.
If no bound exists, the style stays a documented gap.

### codeTable (Phase 2b)

Some systems encode year **and** month in one combined code (e.g. Bosch's
3-character code). That is a style-level field, not a year/month field:

```json
{
  "id": "style-1",
  "pattern": "^...$",
  "codeTable": {
    "positions": [s, e],
    "table": { "K7Q": [2019, 3], "...": [2020, 12] }
  },
  "week": null,
  "examples": [
    { "serial": "...", "expectedYear": 2019, "expectedMonth": 3 }
  ]
}
```

`codeTable` must not coexist with `year`/`month` fields; `week` may still
be present as a separate field. Table values are `[year, month]` pairs
(year plausible, month 1–12). The table must be transcribed completely
from its source chart — a partial table must never ship as if complete,
and the entry count must reconcile against the source.

### rangeTable (Phase 2b)

Some systems encode the year as a numeric band (e.g. Weil-McLain CP
numbers). That is a year field:

```json
{
  "kind": "rangeTable",
  "positions": [s, e],
  "bands": [
    { "min": 1000, "max": 1999, "year": 2020, "approximate": true },
    { "min": 2000, "max": 2999, "year": 2021, "approximate": true }
  ]
}
```

**Overlap rule (never-guess, explicit):** the sliced number is looked up
in every band. Exactly one band → that band's year. Zero bands → the style
does not match. **More than one band → the style does not match** ("cannot
determine"): overlapping bands, and bands fully containing another year's
band, are never resolved by first-match or by picking the earlier year.
A band's `approximate: true` flag (the source states the year is
approximate) is carried on the decode result as `approximate: true` and
must be surfaced by the app; the result is never presented as exact.

## Century disambiguation (two-digit years)

Given two-digit year `YY` and the current year `Y` (at decode time):

1. Candidates are `1900 + YY` and `2000 + YY`.
2. Keep candidates that are `≤ Y` and `≥ yearFloor` (default 1960,
   overridable per style).
3. If exactly one candidate remains, that is the year.
4. Otherwise the year is **ambiguous → the style does not match** (and if
   no style matches, the result is "cannot determine").

Worked logic: with `Y = 2026` and floor 1960, `YY = 97` → 1997 only;
`YY = 20` → 2020 only; `YY = 30` → 1930 (below floor) and 2030 (future) →
ambiguous, correctly, because a `30` serial could be a very old unit or a
future one and the data cannot tell.

## Matching contract ("cannot determine")

Styles are tried in file order. A style **matches** only if:

1. Its `pattern` matches the normalized serial, **and**
2. Every present field extracts and validates (month 1–12, week 1–53,
   year resolves and passes the plausibility check — a dual-candidate
   year list counts as a valid resolution, flagged ambiguous; a
   `rangeTable` number in zero bands or in more than one band does not).

The first matching style wins. If no style matches, the decoder returns
"cannot determine" — never a guessed year, never a partial year presented
as exact. A result may carry year-only (no month/week) when the system
encodes no finer precision; that is exact, not approximate, and is labeled
as year-only.

### Decode result shape (for the future Phase 3 app)

```json
{
  "year": 2022,
  "month": 4,
  "week": null,
  "approximate": false,
  "ambiguous": false
}
```

`year` is an int, or a list of candidate years when `ambiguous` is true.
`approximate` is true only for `rangeTable` bands flagged approximate.
The app must surface both flags honestly: a candidate list is shown as
"either A or B", an approximate year as "about YYYY" — never as a single
exact year.

## Sister-brand reuse

When brand B demonstrably uses brand A's serial system (e.g. ICP-family
brands sharing Carrier's system), B's file sets `usesStylesOf: "a"` and
leaves `styles` empty. The builder copies A's styles into B's built entry
with `"inheritedFrom": "a"`. If A has no styles yet, B fails validation.
Reuse must be evidenced in `notes` (why the systems are shared), not
assumed from a shared parent alone — a shared parent does not prove a
shared serial system.

## What a brand file must never contain

- Building Center prose (paraphrased or copied). Facts only: positions,
  tables, eras, examples, source URL.
- Invented serials as examples. Every example must come from a documented
  source (Building Center page, manufacturer document) or a real data
  plate, cited in `notes` when it is not from the brand's own page.
- A guessed year for an ambiguous serial. See the matching contract.
