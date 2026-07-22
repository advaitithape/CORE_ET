"""Engineering-drawing parser — extract per-operation dimensions & tolerances.

Provider-agnostic by design:
  - default implementation renders each PDF page to an image and asks a vision LLM
    (OpenAI GPT-4o vision) to read dimensions, tolerances and GD&T callouts;
  - the same `DrawingParser` interface can be backed by a dedicated ballooning model
    (YOLO balloon-detection + OCR) in production without changing downstream code.

The drawing pages of CE21609 align one-to-one with process operations, so each
page's dimensions attach to the matching Operation node and feed the C1 check
(drawing tolerance vs. Control-Plan specification).
"""
import base64
import json
import os

# page -> operation number for CE21609 (1-indexed; page 1 is the John-Deere cover).
# Drawing pages follow the process flow, one stage drawing per operation.
PAGE_TO_OP = {
    2: 10, 3: 20, 4: 30, 5: 40, 6: 50, 7: 60, 8: 70, 9: 90, 10: 100, 11: 110,
}

VISION_PROMPT = (
    "You are reading one page of a mechanical engineering drawing for a machined "
    "shaft. Extract every dimensional callout you can see. Return STRICT JSON: "
    '{"dimensions":[{"feature":str,"nominal":number|null,"tol_minus":number|null,'
    '"tol_plus":number|null,"unit":str|null,"gdt":str|null,"raw":str}]}. '
    "Include diameters (Ø), lengths, chamfers, angles, surface finish and GD&T "
    "frames. Use the raw field for the exact text as printed. No prose."
)


def _render_pages(pdf_path, pages, dpi=200):
    """Render selected 1-indexed pages to PNG bytes via pypdfium2 (no poppler needed)."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf_path)
    out = {}
    scale = dpi / 72
    for pno in pages:
        idx = pno - 1
        if idx < 0 or idx >= len(doc):
            continue
        bitmap = doc[idx].render(scale=scale)
        pil = bitmap.to_pil()
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        out[pno] = buf.getvalue()
    return out


def parse(pdf_path="data/CE21609 1.pdf", pages=None):
    """Return {pages:[{page,op_no,dimensions:[...]}], mode}. Falls back to empty
    extraction (no LLM key) so the rest of the pipeline still runs."""
    pages = pages or sorted(PAGE_TO_OP)
    if not os.environ.get("OPENAI_API_KEY"):
        return {"pages": [{"page": p, "op_no": PAGE_TO_OP.get(p), "dimensions": []}
                          for p in pages], "mode": "disabled"}
    from openai import OpenAI
    client = OpenAI()
    imgs = _render_pages(pdf_path, pages)
    results = []
    for p in pages:
        if p not in imgs:
            continue
        b64 = base64.b64encode(imgs[p]).decode()
        try:
            resp = client.chat.completions.create(
                model=os.environ.get("OPENAI_VISION_MODEL", "gpt-4o"),
                temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]}],
            )
            data = json.loads(resp.choices[0].message.content)
            dims = data.get("dimensions", [])
        except Exception as e:  # noqa: BLE001
            dims = [{"error": str(e)}]
        results.append({"page": p, "op_no": PAGE_TO_OP.get(p), "dimensions": dims})
    return {"pages": results, "mode": "openai-vision"}


if __name__ == "__main__":
    import sys
    out = parse(sys.argv[1] if len(sys.argv) > 1 else "data/CE21609 1.pdf")
    print("mode:", out["mode"])
    for pg in out["pages"]:
        print(f"  page {pg['page']} -> Op {pg['op_no']}: {len(pg['dimensions'])} dims")
