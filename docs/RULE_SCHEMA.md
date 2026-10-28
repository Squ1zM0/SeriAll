# SeriAll rule schema (locked for Phase 2 curation)

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
| `sourceUrl` | yes | The brand's Building Center page. Also the app's fallback link. |
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
| `examples` | yes, ≥ 1 | Worked examples. **Every example must decode to its expected values or the builder refuses the brand.** |
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

### Year

- `{ "kind": "digits", "positions": [s, e] }` — the sliced digits are a
  two-digit year `YY`, resolved by the century rule below; or a four-digit
  year, used as-is (must still pass the plausibility check).
- `{ "kind": "letterTable", "positions": [s, e], "table": { "B": 1987, ... } }`
  — the sliced letter(s) map through an explicit table to a full year.
  Tables are curated per brand in Phase 2; the schema requires every key
  to be a single uppercase letter and every value a full four-digit year.
  This is the shape used by letter-year systems (e.g. Trane's year letters).

### Month

- `{ "kind": "digits", "positions": [s, e] }` — sliced digits must be 1–12.
- `{ "kind": "letterTable", "positions": [s, e], "table": { "A": 1, ... } }` —
  explicit letter → month-number map (1 = January). Letter systems that
  skip letters (e.g. Lennox month letters A–M minus I) are expressed by
  simply omitting those letters from the table.

### Week

- `{ "kind": "digits", "positions": [s, e] }` — sliced digits must be 1–53.

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
   year resolves unambiguously and passes the plausibility check).

The first matching style wins. If no style matches, the decoder returns
"cannot determine" — never a guessed year, never a partial year presented
as exact. A result may carry year-only (no month/week) when the system
encodes no finer precision; that is exact, not approximate, and is labeled
as year-only.

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
