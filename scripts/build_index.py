#!/usr/bin/env python3
"""SeriAll builder: validate data/brands/*.json and emit dist/index.json.

Rules (see docs/RULE_SCHEMA.md):
- Files starting with '_' are schema examples and are never built.
- Every example serial must decode to its expected values, or the build
  fails (exit non-zero, no index written).
- 'usesStylesOf' copies another brand's styles, tagged 'inheritedFrom'.
- Decode results: {"year": int | [int, ...], "month": int | None,
  "week": int | None, "approximate": bool, "ambiguous": bool}.
  A list year is an explicit dual-candidate set (cyclic codes), never a
  guess; "ambiguous" is True exactly when the year is such a list.
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


def check_positions(positions, where):
    """Validate a positions value: [s, e] or [[s1, e1], ...]."""
    if (isinstance(positions, list) and len(positions) == 2
            and all(isinstance(x, int) for x in positions)):
        s, e = positions
        if not (0 <= s < e):
            fail(f"{where}: bad positions {positions}")
        return
    if (isinstance(positions, list) and positions
            and all(isinstance(r, list) and len(r) == 2
                    and all(isinstance(x, int) for x in r)
                    for r in positions)):
        for s, e in positions:
            if not (0 <= s < e):
                fail(f"{where}: bad positions {positions}")
        return
    fail(f"{where}: positions must be [s, e] or [[s1, e1], ...], "
         f"got {positions!r}")


def slice_positions(text, positions):
    """Slice text by a single range or a list of ranges (concatenated,
    in order). Returns None when any range is out of bounds."""
    if isinstance(positions[0], int):
        ranges = [positions]
    else:
        ranges = positions
    out = []
    for s, e in ranges:
        if e > len(text):
            return None
        out.append(text[s:e])
    return "".join(out)


def total_slice_len(positions):
    if isinstance(positions[0], int):
        return positions[1] - positions[0]
    return sum(e - s for s, e in positions)


def resolve_year(field, text, floor, current_year):
    """Return (year, approximate) where year is int, a list of candidate
    ints (dual-candidate tables), or None (no match)."""
    kind = field.get("kind")
    positions = field.get("positions")
    chunk = slice_positions(text, positions)
    if chunk is None:
        return None, False
    if kind == "digits":
        if not chunk.isdigit():
            return None, False
        if len(chunk) == 4:
            y = int(chunk)
            return (y, False) if floor <= y <= current_year else (None, False)
        if len(chunk) == 2:
            yy = int(chunk)
            cands = [y for y in (1900 + yy, 2000 + yy)
                     if floor <= y <= current_year]
            return (cands[0], False) if len(cands) == 1 else (None, False)
        return None, False
    if kind == "letterTable":
        table = field.get("table", {})
        val = table.get(chunk)
        if val is None:
            return None, False
        if isinstance(val, list):
            vals = sorted(set(val))
            if len(vals) == 1:
                return vals[0], False
            return vals, False
        return val, False
    if kind == "rangeTable":
        if not chunk.isdigit():
            return None, False
        v = int(chunk)
        matches = [b for b in field.get("bands", [])
                   if b["min"] <= v <= b["max"]]
        if len(matches) != 1:
            # Zero bands: no match. More than one: overlapping bands, and
            # the overlap rule says "cannot determine" — never pick one.
            return None, False
        band = matches[0]
        return band["year"], bool(band.get("approximate", False))
    return None, False


def resolve_int(field, text, lo, hi):
    kind = field.get("kind")
    positions = field.get("positions")
    chunk = slice_positions(text, positions)
    if chunk is None:
        return None
    if kind == "digits":
        if not chunk.isdigit():
            return None
        v = int(chunk)
        return v if lo <= v <= hi else None
    if kind == "letterTable":
        table = field.get("table", {})
        return table.get(chunk)
    return None


def resolve_code_table(code_table, text):
    """codeTable: {"positions": [...], "table": {code: [year, month]}}.
    Returns (year, month) or None."""
    chunk = slice_positions(text, code_table.get("positions"))
    if chunk is None:
        return None
    val = code_table.get("table", {}).get(chunk)
    if val is None:
        return None
    return val[0], val[1]


def decode(style, serial, current_year):
    """Return a result dict or None if the style does not match."""
    text = normalize(serial)
    try:
        if not re.match(style["pattern"], text):
            return None
    except re.error:
        return None
    floor = style.get("yearFloor", 1960)
    month = None
    week = None
    if style.get("codeTable"):
        got = resolve_code_table(style["codeTable"], text)
        if got is None:
            return None
        year, month = got
        approximate = False
    else:
        year, approximate = resolve_year(style["year"], text, floor,
                                         current_year)
        if year is None:
            return None
        if style.get("month"):
            month = resolve_int(style["month"], text, 1, 12)
            if month is None:
                return None
    if style.get("week"):
        week = resolve_int(style["week"], text, 1, 53)
        if week is None:
            return None
    return {"year": year, "month": month, "week": week,
            "approximate": approximate,
            "ambiguous": isinstance(year, list)}


def check_table(table, where, value_kind):
    """Validate a string-keyed table. value_kind: 'year' (int or list of
    ints) or 'month' (int 1-12)."""
    if not isinstance(table, dict) or not table:
        fail(f"{where}: table must be a non-empty object")
    for key, val in table.items():
        if not isinstance(key, str) or not key or key != key.upper():
            fail(f"{where}: table key {key!r} must be a non-empty "
                 f"uppercase string")
        if value_kind == "year":
            vals = val if isinstance(val, list) else [val]
            if not vals or not all(isinstance(v, int) for v in vals):
                fail(f"{where}: table value for {key!r} must be an int "
                     f"or a list of ints")
            for v in vals:
                if not (1900 <= v <= 2100):
                    fail(f"{where}: table year {v} for {key!r} implausible")
        else:
            if not isinstance(val, int) or not (1 <= val <= 12):
                fail(f"{where}: table month for {key!r} must be 1-12")


def validate_field(field, where, field_kind):
    kind = field.get("kind")
    positions = field.get("positions")
    if positions is None:
        fail(f"{where}: missing 'positions'")
    check_positions(positions, where)
    if kind == "digits":
        # The 2-or-4 rule applies to YEAR digits only: a single-digit year
        # must use an explicit digit-keyed table, not a computed decade
        # rule. Month/week digits may legitimately be 1–2 characters
        # (month 1–12, week 1–53) and are range-checked at decode time.
        if field_kind == "year" and total_slice_len(positions) not in (2, 4):
            fail(f"{where}: year 'digits' needs a 2- or 4-character slice "
                 f"(single-digit years must use an explicit digit-keyed "
                 f"table, not a computed decade rule)")
    elif kind == "letterTable":
        check_table(field.get("table"), where,
                    "year" if field_kind == "year" else "month")
    elif kind == "rangeTable":
        if field_kind != "year":
            fail(f"{where}: 'rangeTable' is only valid for year")
        bands = field.get("bands")
        if not isinstance(bands, list) or not bands:
            fail(f"{where}: 'rangeTable' needs a non-empty 'bands' list")
        for b in bands:
            if not isinstance(b, dict) or "min" not in b \
                    or "max" not in b or "year" not in b:
                fail(f"{where}: each band needs min, max, year")
            if not (isinstance(b["min"], int)
                    and isinstance(b["max"], int)
                    and b["min"] <= b["max"]):
                fail(f"{where}: bad band range {b!r}")
            if not (isinstance(b["year"], int)
                    and 1900 <= b["year"] <= 2100):
                fail(f"{where}: bad band year {b!r}")
    else:
        fail(f"{where}: unknown kind {kind!r}")


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
        where = f"{path} style {st.get('id')}"
        try:
            re.compile(st["pattern"])
        except re.error as exc:
            fail(f"{where}: bad pattern: {exc}")
        if st.get("codeTable"):
            if st.get("year") or st.get("month"):
                fail(f"{where}: 'codeTable' must not coexist with "
                     f"'year'/'month' fields")
            ct = st["codeTable"]
            check_positions(ct.get("positions"), where + " codeTable")
            table = ct.get("table")
            if not isinstance(table, dict) or not table:
                fail(f"{where}: 'codeTable' needs a non-empty 'table'")
            for code, val in table.items():
                if not isinstance(code, str) or not code \
                        or code != code.upper():
                    fail(f"{where}: codeTable key {code!r} must be a "
                         f"non-empty uppercase string")
                if not (isinstance(val, list) and len(val) == 2
                        and isinstance(val[0], int)
                        and isinstance(val[1], int)
                        and 1900 <= val[0] <= 2100
                        and 1 <= val[1] <= 12):
                    fail(f"{where}: codeTable value for {code!r} must be "
                         f"[year, month]")
        else:
            if not st.get("year"):
                fail(f"{where}: missing 'year' (or 'codeTable')")
            validate_field(st["year"], where + " year", "year")
        if st.get("month"):
            validate_field(st["month"], where + " month", "month")
        if st.get("week"):
            validate_field(st["week"], where + " week", "week")
        if not st.get("examples"):
            fail(f"{where}: need >= 1 example")


def years_equal(got, expected):
    """Compare a decoded year (int or candidate list) with an expected
    year (int or candidate list)."""
    got_list = sorted(got if isinstance(got, list) else [got])
    exp_list = sorted(expected if isinstance(expected, list) else [expected])
    return got_list == exp_list


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
                ey = ex["expectedYear"]
                if not years_equal(got["year"], ey):
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"decoded year={got['year']}, expected year={ey}")
                em = ex.get("expectedMonth")
                if em is not None and got["month"] != em:
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"decoded month={got['month']}, expected month={em}")
                ew = ex.get("expectedWeek")
                if ew is not None and got["week"] != ew:
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"decoded week={got['week']}, expected week={ew}")
                ea = ex.get("expectedApproximate")
                if ea is not None and got["approximate"] != ea:
                    fail(f"{slug} style {st['id']}: example {ex['serial']} "
                         f"decoded approximate={got['approximate']}, "
                         f"expected approximate={ea}")
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
