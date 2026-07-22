"""Parse the PFMEA .xls -> per-operation failure lines.

Column layout (header rows 5-10), data from row 11:
  c0  Operation number (merged per op block)
  c1  Process Function / Requirements (merged per failure-mode group)
  c2  Potential Failure Mode (merged per group)
  c3  Potential Effect(s) of Failure
  c4  Severity (S)
  c6  Cause / Mechanism of failure
  c7  Occurrence (O)
  c8  Current process control - prevention
  c9  Current process control - detection
  c10 Detection (D)
  c11 RPN
  c12 Recommended Actions
  c13 Responsibility
"""
import warnings
warnings.filterwarnings("ignore")
import xlrd
from .common import norm_op, clean, to_float, xls_merged_map, xls_cell

C_OP, C_FUNC, C_MODE, C_EFFECT, C_SEV = 0, 1, 2, 3, 4
C_CAUSE, C_OCC, C_PREV, C_DET, C_DETV, C_RPN = 6, 7, 8, 9, 10, 11
C_RECACT, C_RESP = 12, 13
DATA_START = 11


def parse(path):
    wb = xlrd.open_workbook(path, formatting_info=True)
    sh = wb.sheet_by_index(0)
    mmap = xls_merged_map(sh)

    lines = []
    for r in range(DATA_START, sh.nrows):
        rpn = to_float(xls_cell(sh, mmap, r, C_RPN))
        cause = clean(xls_cell(sh, mmap, r, C_CAUSE))
        mode = clean(xls_cell(sh, mmap, r, C_MODE))
        # a real failure line has an RPN or at least a cause+mode
        if rpn is None and not (cause or mode):
            continue
        op_no = norm_op(xls_cell(sh, mmap, r, C_OP))
        if op_no is None:
            continue
        rec = clean(xls_cell(sh, mmap, r, C_RECACT))
        lines.append({
            "op_no": op_no,
            "function": clean(xls_cell(sh, mmap, r, C_FUNC)),
            "failure_mode": mode,
            "effect": clean(xls_cell(sh, mmap, r, C_EFFECT)),
            "severity": to_float(xls_cell(sh, mmap, r, C_SEV)),
            "cause": cause,
            "occurrence": to_float(xls_cell(sh, mmap, r, C_OCC)),
            "prevention": clean(xls_cell(sh, mmap, r, C_PREV)),
            "detection": clean(xls_cell(sh, mmap, r, C_DET)),
            "detection_val": to_float(xls_cell(sh, mmap, r, C_DETV)),
            "rpn": rpn,
            "recommended_action": rec,
            "responsibility": clean(xls_cell(sh, mmap, r, C_RESP)),
            "source": {"doc": "PFMEA", "sheet": sh.name, "row": r},
        })
    return {"lines": lines}


if __name__ == "__main__":
    import json, sys
    out = parse(sys.argv[1] if len(sys.argv) > 1 else "data/CE21609_ PFMEA 2.xls")
    print(f"lines={len(out['lines'])}")
    print(json.dumps(out["lines"][:4], indent=2, ensure_ascii=False))
