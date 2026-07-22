"""Shared helpers for the APQP Digital Thread extraction pipeline."""
import re


def norm_op(val):
    """Normalize an operation number to a canonical int (e.g. '10.0' -> 10, '20.Bar' -> 20).

    Returns None if no operation number can be parsed.
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("---", "--", "----"):
        return None
    m = re.match(r"\s*0*(\d+)", s)
    if not m:
        return None
    return int(m.group(1))


def clean(val):
    """Collapse whitespace/newlines into a single readable string."""
    if val is None:
        return ""
    s = str(val).replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def to_float(val):
    if val is None:
        return None
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None


# --- merged-cell fill helpers -------------------------------------------------

def xls_merged_map(sheet):
    """Map every (row,col) inside an xlrd merged range to its top-left value."""
    m = {}
    for (rlo, rhi, clo, chi) in sheet.merged_cells:
        top = sheet.cell_value(rlo, clo)
        for r in range(rlo, rhi):
            for c in range(clo, chi):
                m[(r, c)] = top
    return m


def xls_cell(sheet, mmap, r, c):
    """Value at (r,c), resolving merged ranges (xlrd)."""
    if (r, c) in mmap:
        return mmap[(r, c)]
    if r < sheet.nrows and c < sheet.ncols:
        return sheet.cell_value(r, c)
    return ""


def xlsx_merged_map(ws):
    """Map every (row,col) inside an openpyxl merged range to its top-left value.

    Rows/cols are 1-indexed to match openpyxl.
    """
    m = {}
    for rng in ws.merged_cells.ranges:
        top = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                m[(r, c)] = top
    return m


def xlsx_cell(ws, mmap, r, c):
    if (r, c) in mmap:
        return mmap[(r, c)]
    return ws.cell(r, c).value


# --- specification / tolerance parsing ---------------------------------------

_NUM = r"[-+]?\d+(?:\.\d+)?"


def parse_spec(spec):
    """Best-effort extraction of a numeric interval from a control-plan / drawing spec.

    Returns dict {nominal, low, high, unit, raw, kind} or None. Handles common forms:
      '30/32 MM', '0.18 - 0.23', '±0.2', '200 ±0.3', '1% Max', '5:1 min', 'Ø30/32'.
    """
    if spec is None:
        return None
    raw = clean(spec)
    if not raw:
        return None
    txt = raw.replace("Ø", "").replace("∅", "")
    unit_m = re.search(r"(mm|MM|micron|µm|deg|HRC|HV)", raw)
    unit = unit_m.group(1).lower() if unit_m else None

    # nominal ± tol   e.g. "200 ±0.3"  or  "1.65 ±0.2"
    m = re.search(rf"({_NUM})\s*(?:±|\+/-|±)\s*({_NUM})", txt)
    if m:
        nom, tol = float(m.group(1)), float(m.group(2))
        return {"raw": raw, "unit": unit, "kind": "sym_tol",
                "nominal": nom, "low": nom - tol, "high": nom + tol}

    # range  e.g. "0.18 - 0.23"  or  "30/32"
    m = re.search(rf"({_NUM})\s*(?:-|/|to)\s*({_NUM})", txt)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        lo, hi = min(a, b), max(a, b)
        return {"raw": raw, "unit": unit, "kind": "range",
                "nominal": (lo + hi) / 2, "low": lo, "high": hi}

    # single bound  e.g. "1% Max", "0.030 Max", "≥5"
    m = re.search(rf"({_NUM})\s*(?:%?\s*)(max|min)?", txt, re.I)
    if m:
        v = float(m.group(1))
        bound = (m.group(2) or "").lower()
        d = {"raw": raw, "unit": unit, "kind": "single", "nominal": v,
             "low": None, "high": None}
        if bound == "max":
            d["high"] = v
        elif bound == "min":
            d["low"] = v
        return d
    return None
