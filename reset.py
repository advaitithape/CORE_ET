"""Reset the Industrial Knowledge Intelligence system to zero documents.

Run anytime:   python reset.py
Clears the ingestion manifest and uploaded files, and (if the backend is running)
resets the live system immediately. Otherwise the empty state applies on next start.
"""
import json
import os
import shutil
import urllib.request

MANIFEST = os.path.join("outputs", "ingested.json")

os.makedirs("outputs", exist_ok=True)
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump([], f)

uploads = os.path.join("data", "uploads")
if os.path.isdir(uploads):
    shutil.rmtree(uploads)
os.makedirs(uploads, exist_ok=True)

try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/reset", method="POST", data=b"")
    urllib.request.urlopen(req, timeout=4)
    print("[OK] Live backend reset - knowledge base is now empty.")
except Exception:
    print("[OK] Manifest cleared. (Start/restart the backend for the empty state to apply.)")

print("System reset to 0 documents. Add documents from the UI to build it up again.")
