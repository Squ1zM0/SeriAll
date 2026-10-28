# SeriAll

**HVAC serial-number age-decoding rules for the Price-Cal "HVAC Age" page.**

SeriAll is the stored-rules data repo behind a simple idea: a technician types a
brand and a serial number, and the app tells them when the unit was made and
roughly how old it is.

## Architecture (decided Oct 28, 2026)

- **Stored rules, not live queries.** Building Intelligence Center
  (building-center.org) publishes per-brand serial-decoding guides, but those
  pages are prose with color-coded legends, not an API. Runtime parsing of
  them would be fragile, and the decoding logic would be needed either way.
  So the rules live here, curated as data, and Price-Cal fetches the built
  index live — the same data/app split as SupplyFind, TechDirect, and
  ManuAll.
- **Decoding happens client-side.** The app downloads the rule index and
  decodes the serial on the phone. **A serial number never leaves the
  device.** No serial is stored, logged, or sent to any server by this repo
  or by the decoding step.
- **Fallback link.** When no rule matches a brand/serial, the app links to
  that brand's Building Center page so the technician can read the guide
  directly, instead of being given a guessed year.

## Data / app split

- Rules live **here** (SeriAll). App behavior lives in **Price-Cal**.
- A rule change here reaches the app on its next index fetch — no Price-Cal
  redeploy is needed for data updates.
- Price-Cal changes are out of scope for this repo.

## Attribution

Rules in this repo encode **facts** from Building Intelligence Center brand
pages — serial positions → year/month/week — never copied prose. Every brand
file links back to its Building Center page in `sourceUrl`, as both the
source of the rule and the fallback for the user. If a rule is wrong, the
Building Center page is the authority to check against.

## Validation rule (non-negotiable)

- Every example serial in a brand file **must decode to its expected date**
  before that brand ships. The builder (`scripts/build_index.py`) enforces
  this and refuses to build otherwise.
- A serial that matches no style, or whose extracted fields fail validation
  (impossible month/week, implausible year), returns **"cannot determine"**
  — never a guessed year. A wrong age on a quote is worse than no age.

## Status

**Phase 1: scaffold + inventory only. No curated brand rules yet.**

- `docs/RULE_SCHEMA.md` — the rule schema, locked for Phase 2 curation.
- `data/brands/` — per-brand rule files (JSON). Only `_example.json` exists
  so far, and it is clearly marked as a schema example, not a shipped rule.
- `inventory/hvac_brands_building_center.md` — the Building Center HVAC
  brand list (names + page URLs + family groupings only, no copied prose),
  plus the proposed V1 majors shortlist awaiting approval.
- `scripts/build_index.py` — validates brand files and builds
  `dist/index.json` from them. With no real brand files yet, there is no
  built index to ship; `dist/` holds only a placeholder.

Phase 2 will curate rules brand by brand, each with example validation, for
the approved V1 majors shortlist.
