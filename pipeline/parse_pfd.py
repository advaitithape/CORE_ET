"""Parse the Process Flow Diagram (PFD) .xls -> operation spine."""
import warnings
warnings.filterwarnings("ignore")
import xlrd
from .common import norm_op, clean, xls_merged_map, xls_cell

# Column layout (sheet 'PFD'), header at row 6:
#  c0 OPERATION NUMBER | c1 OPERATION DESCRIPTION | c3 PRODUCT CHARACTERISTIC
#  c4 PROCESS CHARACTERISTIC | c5 CONTROL PLAN REF. NO
COL_OP, COL_DESC, COL_PROD, COL_PROC, COL_CP = 0, 1, 3, 4, 5


def parse(path):
    wb = xlrd.open_workbook(path, formatting_info=True)
    sh = wb.sheet_by_index(0)
    mmap = xls_merged_map(sh)

    meta = {}
    for r in range(0, 6):
        row = [clean(xls_cell(sh, mmap, r, c)) for c in range(sh.ncols)]
        for i, v in enumerate(row):
            if "PART NO" in v.upper():
                meta["part_no"] = clean(row[i + 1]) if i + 1 < len(row) else ""
            if "PART NAME" in v.upper():
                meta["part_name"] = clean(row[i + 1]) if i + 1 < len(row) else ""

    operations = []
    for r in range(7, sh.nrows):
        raw_op = clean(xls_cell(sh, mmap, r, COL_OP))
        op_no = norm_op(raw_op)
        desc = clean(xls_cell(sh, mmap, r, COL_DESC))
        if op_no is None and not desc:
            continue
        cp = clean(xls_cell(sh, mmap, r, COL_CP)).lstrip("'")
        operations.append({
            "op_no": op_no,
            "op_label": raw_op,
            "name": desc,
            "product_char": clean(xls_cell(sh, mmap, r, COL_PROD)),
            "process_char": clean(xls_cell(sh, mmap, r, COL_PROC)),
            "cp_ref": cp if cp and cp not in ("---", "--") else None,
            "source": {"doc": "PFD", "sheet": sh.name, "row": r},
        })
    return {"meta": meta, "operations": operations}


if __name__ == "__main__":
    import json, sys
    out = parse(sys.argv[1] if len(sys.argv) > 1 else
                "data/CE21609_ Process Flow Chart 2.xls")
    print(json.dumps(out, indent=2, ensure_ascii=False)[:3000])
