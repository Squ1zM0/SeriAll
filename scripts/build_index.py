#!/usr/bin/env python3
"""SeriAll builder: validate data/brands/*.json and emit dist/index.json.

Rules (see docs/RULE_SCHEMA.md):
- Files starting with '_' are schema examples and are never built.
- Every example serial must decode to its expected values, or the build
  fails (exit non-zero, no index written).
- 'usesStylesOf' copies another brand's styles, tagged 'inheritedFrom'.
- Output is deterministic: no timestamps, brands sorted by slug.

Usage: python3 scripts/build_index.py [--root <repo-root>]
"""
import datetime
import json
import re
import sys
from pathlib import Path


def fail(msg):
    print(f"build_index: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def normalize(serial):
    return re.sub(r"[\s\-]+", "", serial.upper())


def resolve_year(field, text, year_floor, current_year):
    kind = field.get("kind")
    s, e = field["positions"]
    chunk = text[s:e]
    if kind == "digits":
        if not chunk.isdigit():
            return None
        if len(chunk) == 4:
            y = int(chunk)
            return y if year_floor <= y <= current_year else None
        if len(chunk) == 2:
            yy = int(chunk)
            cands = [y for y in (1900 + yy, 2000 + yy)
                     if year_floor <= y <= current_year]
            return cands[0] if len(cands) == 1 else None
        return None
    if kind == "letterTable":
        table = field.get("table", {})
        return table.get(chunk)
    return None


def resolve_int(field, text, lo, hi):
    kind = field.get("kind")
    s, e = field["positions"]
    chunk = text[s:e]
    if kind == "digits":
        if not chunk.isdigit():
            return None
        v = int(chunk)
        return v if lo <= v <= hi else None
    if kind == "letterTable":
        table = field.get("table", {})
        return table.get(chunk)
    return None


def decode(style, serial, current_year):
    """Return (year, month, week) or None if the style does not match."""
    text = normalize(serial)
    try:
        if not re.match(style["pattern"], text):
            return None
    except re.error:
        return None
    floor = style.get("yearFloor", 1960)
    year = resolve_year(style["year"], text, floor, current_year)
    if year is None:
        return None
    month = None
    if style.get("month"):
        month = resolve_int(style["month"], text, 1, 12)
        if month is None:
            return None
    week = None
    if style.get("week"):
        week = resolve_int(style["week"], text, 1, 53)
        if week is None:
            return None
    return (year, month, week)


def validate_brand(data, path):
    for f in ("brand", "slug", "sourceUrl"):
        if not data.get(f):
            fail(f"{path}: missing required field '{f}'")
    styles = data.get("styles") or []
    uses = data.get("usesStylesOf")
    if uses and styles:
        fail(f"{path}: 'usesStylesOf' and 'styles' must not both be set")
    if not uses and not styles:
        fail(f"{path}: need 'styles' or 'usesStylesOf'")
    for st in styles:
        try:
            re.compile(st["pattern"])
        except re.error as exc:
            fail(f"{path} style {st.get('id')}: bad pattern: {exc}")
        if not st.get("year"):
            fail(f"{path} style {st.get('id')}: missing 'year'")
        if not st.get("examples"):
            fail(f"{path} style {st.get('id')}: need >= 1 example")


def main():
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else Path(__file__).resolve().parent.parent
    brands_dir = root / "data" / "brands"
    out_path = root / "dist" / "index.json"
    current_year = datetime.date.today().year
    raw = {}
    for p in sorted(brands_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            raw[json.loads(p.read_text())["slug"]] = json.loads(p.read_text())
        except Exception as exc:
            fail(f"{p.name}: invalid JSON: {exc}")
    built = {}
    for slug, data in raw.items():
        validate_brand(data, slug)
    for slug, data in sorted(raw.items()):
        if data.get("usesStylesOf"):
            target = data["usesStylesOf"]
            if target not in raw or not raw[target].get("styles"):
                fail(f"{slug}: 'usesStylesOf' target '{target}' has no styles")
            styles = [dict(st, inheritedFrom=target)
                      for st in raw[target]["styles"]]
        else:
            styles = data["styles"]
        # Example validation: every example must decode to its expectation.
        for st in styles:
            for ex in st.get("examples", []):
                got = decode(st, ex["serial"], current_year)
                if got is None:
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"does not decode (expected {ex})")
                ey, em = ex["expectedYear"], ex.get("expectedMonth")
                if got[0] != ey or (em is not None and got[1] != em):
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"decoded {got}, expected year={ey} month={em}")
        entry = {k: data.get(k) for k in
                 ("brand", "slug", "aliases", "parent", "sisters",
                  "sourceUrl", "notes")}
        entry["styles"] = styles
        built[slug] = entry
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "brandCount": len(built), "brands": built}
    out_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(f"build_index: {len(built)} brands -> {out_path}")


if __name__ == "__main__":
    main()
