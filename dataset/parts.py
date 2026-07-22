"""Canonical demo dataset — three parts across two real process domains.

Part 1  CE21609  Pinion Shaft         (steel machining)      — real APQP files in data/
Part 2  S-10254  Base                 (aluminium die-cast)   — from real BASE IR + Hindi WI
Part 3  YF-4021  Yoke Flange          (steel forge+machine)  — new, plausible

Each part carries: metadata, operations (with characteristics + specs), PFMEA failure
modes, and the QMS records (inward / in-process / PDIR inspection, NCR/CAR, 8D CAPA,
work instruction). Parts 2 & 3 are emitted as filled documents by dataset/generate.py
and flow through the same pipeline; Part 1's APQP comes from its real files.
"""

# ---------------------------------------------------------------------------
# PART 2 — BASE (aluminium high-pressure die casting)
# grounded in the real BASE IR.xlsx (dims, temps) + Hindi PDC work instruction
# ---------------------------------------------------------------------------
BASE = {
    "part_no": "S-10254-5",
    "part_name": "Base",
    "customer": "Four Front Pvt. Ltd.",
    "supplier": "Shivkrupa Industries",
    "material": "ADC 12 (Aluminium alloy)",
    "process_type": "High Pressure Die Casting",
    "operations": [
        {"op_no": 10, "name": "Melting & Metal Preparation", "machine": "Melting Furnace",
         "cp_ref": "CP/BASE/01",
         "product_chars": [
            {"name": "Melt composition (Al-Si)", "spec": "ADC12 as per JIS H5302", "special": ""},
         ],
         "process_chars": [
            {"name": "Furnace temperature", "spec": "620-675", "unit": "°C", "low": 620, "high": 675, "nominal": 647.5},
            {"name": "Degassing time", "spec": "8-12 min", "unit": "min", "low": 8, "high": 12, "nominal": 10},
         ]},
        {"op_no": 20, "name": "Die Casting (PDC)", "machine": "80T / 200T Cold Chamber PDC",
         "cp_ref": "CP/BASE/02",
         "product_chars": [
            {"name": "Weight", "spec": "101", "unit": "gm", "low": 98, "high": 104, "nominal": 101, "special": "CC"},
            {"name": "DIM1 Overall length", "spec": "134±0.2", "unit": "mm", "low": 133.8, "high": 134.2, "nominal": 134},
            {"name": "DIM2 Width", "spec": "116.4±0.1", "unit": "mm", "low": 116.3, "high": 116.5, "nominal": 116.4},
            {"name": "DIM7 Boss height", "spec": "63.6±0.1", "unit": "mm", "low": 63.5, "high": 63.7, "nominal": 63.6},
         ],
         "process_chars": [
            {"name": "Die temperature", "spec": "220-295", "unit": "°C", "low": 220, "high": 295, "nominal": 257},
            {"name": "Injection pressure", "spec": "70-90 bar", "unit": "bar", "low": 70, "high": 90, "nominal": 80},
         ]},
        {"op_no": 30, "name": "Trimming", "machine": "Trimming Press 40T", "cp_ref": "CP/BASE/03",
         "product_chars": [
            {"name": "Flash removal", "spec": "No flash > 0.3 mm", "unit": "mm", "high": 0.3, "nominal": 0},
         ], "process_chars": []},
        {"op_no": 40, "name": "Shot Blasting", "machine": "Shot Blasting M/c", "cp_ref": "CP/BASE/04",
         "product_chars": [
            {"name": "Surface finish", "spec": "Uniform matt, no adhering shot", "special": ""},
         ], "process_chars": [
            {"name": "Blasting time", "spec": "6-10 min", "unit": "min", "low": 6, "high": 10, "nominal": 8},
         ]},
        {"op_no": 50, "name": "CNC Machining & Drilling", "machine": "VMC", "cp_ref": "CP/BASE/05",
         "product_chars": [
            {"name": "DIM5 Tapped hole", "spec": "4-M3x0.5", "special": "SC"},
            {"name": "DIM6 Step", "spec": "2.5±0.1", "unit": "mm", "low": 2.4, "high": 2.6, "nominal": 2.5},
            {"name": "DIM9 Bore", "spec": "49±0.2", "unit": "mm", "low": 48.8, "high": 49.2, "nominal": 49},
         ], "process_chars": [
            {"name": "Spindle speed", "spec": "2500-3000 rpm", "unit": "rpm", "low": 2500, "high": 3000, "nominal": 2750},
         ]},
        {"op_no": 60, "name": "Deburring", "machine": "Manual / Vibro", "cp_ref": "CP/BASE/06",
         "product_chars": [{"name": "Burr free edges", "spec": "No sharp burrs", "special": ""}], "process_chars": []},
        {"op_no": 70, "name": "Final Inspection", "machine": "CMM / Gauges", "cp_ref": "CP/BASE/07",
         "product_chars": [
            {"name": "All dimensions", "spec": "As per drawing", "special": ""},
            {"name": "Leak test", "spec": "No leakage @ 2 bar", "unit": "bar", "nominal": 2, "special": "CC"},
         ], "process_chars": []},
        {"op_no": 80, "name": "Washing & Packing", "machine": "Washing M/c", "cp_ref": "CP/BASE/08",
         "product_chars": [{"name": "Cleanliness", "spec": "Free from oil, dust", "special": ""}], "process_chars": []},
    ],
    "failure_modes": [
        {"op_no": 10, "failure_mode": "Gas porosity in melt", "effect": "Porosity in casting, leakage",
         "severity": 8, "cause": "Improper degassing / high hydrogen", "occurrence": 4,
         "prevention": "Degassing as per WI, rotary degasser", "detection": "Reduced pressure test per heat",
         "detection_val": 4, "rpn": 128, "recommended_action": "Automate degassing cycle time control"},
        {"op_no": 20, "failure_mode": "Weight low (short shot)", "effect": "Incomplete fill, part reject",
         "severity": 7, "cause": "Low injection pressure / low metal temp", "occurrence": 5,
         "prevention": "Pressure & temp monitoring per WI", "detection": "100% weight check on WS",
         "detection_val": 3, "rpn": 105, "recommended_action": ""},
        {"op_no": 20, "failure_mode": "Cold shut / flow lines", "effect": "Surface defect, weak part",
         "severity": 7, "cause": "Low die temperature", "occurrence": 4,
         "prevention": "Die pre-heat, pyrometer check", "detection": "Visual + first-piece",
         "detection_val": 4, "rpn": 112, "recommended_action": "Install die-temp interlock"},
        {"op_no": 20, "failure_mode": "Dimensional oversize DIM1", "effect": "Assembly interference",
         "severity": 6, "cause": "Die wear / flash", "occurrence": 3,
         "prevention": "Die maintenance schedule", "detection": "Vernier check per frequency",
         "detection_val": 3, "rpn": 54, "recommended_action": ""},
        {"op_no": 50, "failure_mode": "Tapped hole undersize (M3)", "effect": "Fastener will not seat",
         "severity": 8, "cause": "Worn tap / wrong tap", "occurrence": 3,
         "prevention": "Tool life monitoring", "detection": "Thread plug gauge",
         "detection_val": 3, "rpn": 72, "recommended_action": ""},
        {"op_no": 70, "failure_mode": "Leak at boss", "effect": "Field failure — coolant leak",
         "severity": 9, "cause": "Sub-surface porosity from casting", "occurrence": 3,
         "prevention": "Process controls at Op 10/20", "detection": "100% leak test",
         "detection_val": 2, "rpn": 54, "recommended_action": "Link leak rejects to melt degassing records"},
    ],
    "wi": {"op_no": 20, "language": "Hindi", "title": "PDC Machine Operation (SI-L-06)",
           "source_file": "Work Instruction SI-L-06 Hindi1.docx",
           "steps_en": [
               "Understand from supervisor how to operate the machine first.",
               "Before starting production, check all parameters; if any is wrong, get it corrected via supervisor.",
               "Set the pouring-ladle size according to the loaded die.",
               "Fit insert pins correctly for dies that need them.",
               "Apply water-based die-coat and air as required, then close the die carefully.",
               "Pour metal carefully into the sleeve; press the shot button immediately after pouring.",
               "As the die unlocks and ejects, remove the casting using the gripper.",
               "Check whether the casting is OK; place it gently on the trolley to avoid dents/damage.",
               "If repeated rejection occurs during production, inform the quality engineer or supervisor.",
               "Apply block die-coat on the plunger after every shot; follow all safety rules.",
           ]},
}

# ---------------------------------------------------------------------------
# PART 3 — YOKE FLANGE (steel forging + machining) — new plausible part
# ---------------------------------------------------------------------------
YOKE = {
    "part_no": "YF-4021",
    "part_name": "Yoke Flange",
    "customer": "Tata Motors Ltd.",
    "supplier": "Shivkrupa Industries",
    "material": "EN8D (Carbon Steel)",
    "process_type": "Forging + Machining",
    "operations": [
        {"op_no": 10, "name": "Raw Material Inspection", "machine": "Incoming QA", "cp_ref": "CP/YF/01",
         "product_chars": [{"name": "Bar diameter", "spec": "Ø55±0.5", "unit": "mm", "low": 54.5, "high": 55.5, "nominal": 55},
                            {"name": "Material grade", "spec": "EN8D as per BS970", "special": ""}],
         "process_chars": []},
        {"op_no": 20, "name": "Forging", "machine": "Forging Hammer 2T", "cp_ref": "CP/YF/02",
         "product_chars": [{"name": "Forged flange OD", "spec": "Ø120±1.0", "unit": "mm", "low": 119, "high": 121, "nominal": 120}],
         "process_chars": [{"name": "Forging temperature", "spec": "1100-1200", "unit": "°C", "low": 1100, "high": 1200, "nominal": 1150}]},
        {"op_no": 30, "name": "Normalizing (Heat Treatment)", "machine": "HT Furnace", "cp_ref": "CP/YF/03",
         "product_chars": [{"name": "Hardness", "spec": "197-255 BHN", "unit": "BHN", "low": 197, "high": 255, "nominal": 226, "special": "SC"}],
         "process_chars": [{"name": "Soaking temperature", "spec": "860-890", "unit": "°C", "low": 860, "high": 890, "nominal": 875}]},
        {"op_no": 40, "name": "CNC Turning", "machine": "CNC Lathe", "cp_ref": "CP/YF/04",
         "product_chars": [{"name": "Spigot diameter", "spec": "Ø80.00-79.95", "unit": "mm", "low": 79.95, "high": 80.0, "nominal": 79.975, "special": "CC"},
                           {"name": "Flange thickness", "spec": "18±0.1", "unit": "mm", "low": 17.9, "high": 18.1, "nominal": 18}],
         "process_chars": [{"name": "Cutting speed", "spec": "180-220 m/min", "unit": "m/min", "low": 180, "high": 220, "nominal": 200}]},
        {"op_no": 50, "name": "Drilling (Bolt Holes)", "machine": "VMC", "cp_ref": "CP/YF/05",
         "product_chars": [{"name": "4 x bolt hole PCD", "spec": "Ø100±0.1", "unit": "mm", "low": 99.9, "high": 100.1, "nominal": 100},
                           {"name": "Bolt hole dia", "spec": "4-Ø10.5±0.1", "unit": "mm", "low": 10.4, "high": 10.6, "nominal": 10.5}],
         "process_chars": []},
        {"op_no": 60, "name": "Broaching (Spline)", "machine": "Broaching M/c", "cp_ref": "CP/YF/06",
         "product_chars": [{"name": "Spline major dia", "spec": "Ø32H7", "unit": "mm", "low": 32.0, "high": 32.025, "nominal": 32.012, "special": "CC"}],
         "process_chars": []},
        {"op_no": 70, "name": "Final Inspection", "machine": "CMM", "cp_ref": "CP/YF/07",
         "product_chars": [{"name": "All dimensions", "spec": "As per drawing", "special": ""}], "process_chars": []},
        {"op_no": 80, "name": "Phosphating & Packing", "machine": "Phosphating line", "cp_ref": "CP/YF/08",
         "product_chars": [{"name": "Coating", "spec": "Zinc phosphate 5-10 µm", "unit": "µm", "low": 5, "high": 10, "nominal": 7.5}], "process_chars": []},
    ],
    "failure_modes": [
        {"op_no": 20, "failure_mode": "Forging lap / fold", "effect": "Crack initiation in service",
         "severity": 9, "cause": "Improper die fill / low temp", "occurrence": 3,
         "prevention": "Temp control, die design", "detection": "MPI on sample", "detection_val": 4, "rpn": 108,
         "recommended_action": "100% MPI on critical batches"},
        {"op_no": 30, "failure_mode": "Hardness out of range", "effect": "Poor machinability / wear",
         "severity": 7, "cause": "Furnace temp deviation", "occurrence": 3,
         "prevention": "Furnace calibration", "detection": "Hardness test per lot", "detection_val": 3, "rpn": 63,
         "recommended_action": ""},
        {"op_no": 40, "failure_mode": "Spigot diameter oversize", "effect": "Loose fit, NVH at assembly",
         "severity": 8, "cause": "Tool wear, offset drift", "occurrence": 4,
         "prevention": "Tool-life monitoring, SPC", "detection": "Air gauge 100%", "detection_val": 3, "rpn": 96,
         "recommended_action": ""},
        {"op_no": 50, "failure_mode": "PCD position error", "effect": "Bolt holes misaligned at assembly",
         "severity": 8, "cause": "Fixture wear", "occurrence": 3,
         "prevention": "Fixture check", "detection": "Position gauge", "detection_val": 4, "rpn": 96,
         "recommended_action": "Poka-yoke fixture with sensor"},
        {"op_no": 60, "failure_mode": "Spline oversize (fails ring gauge)", "effect": "No-assembly with shaft",
         "severity": 9, "cause": "Broach wear", "occurrence": 3,
         "prevention": "Broach life count", "detection": "GO/NO-GO spline gauge", "detection_val": 2, "rpn": 54,
         "recommended_action": ""},
    ],
    "wi": {"op_no": 40, "language": "English", "title": "CNC Turning Operation (WI-YF-04)",
           "steps_en": [
               "Verify job setup and datum against the setup sheet before starting.",
               "Load the correct CNC program (YF-4021-OP40) and confirm the revision.",
               "Check tool offsets and insert condition; replace inserts at the defined tool-life count.",
               "Run the first piece and get it approved by QA before series production.",
               "Monitor the spigot diameter with the air gauge every 5th part (SPC).",
               "If the trend approaches the control limit, correct the offset and inform the supervisor.",
               "Deburr and place parts in the bin without contact damage.",
           ]},
}

# ---------------------------------------------------------------------------
# QMS records (all three parts) — inspection reports, NCR/CAR, 8D CAPA
# Part 1 (Pinion) uses its real operations; here we attach quality records.
# ---------------------------------------------------------------------------

# Inward inspection (incoming raw material / bought-out)
INWARD = {
    "S-10254-5": {"supplier": "Metalex Alloys", "date": "2026-06-12", "material": "ADC12 ingot",
        "params": [
            {"param": "Chemical composition (Si)", "spec": "9.6-12.0 %", "mode": "Spectro", "obs": ["10.8", "10.9", "10.7"], "status": "Accepted"},
            {"param": "Ingot cleanliness", "spec": "Free from dross", "mode": "Visual", "obs": ["OK", "OK", "OK"], "status": "Accepted"},
            {"param": "Ingot weight", "spec": "6-8 kg", "mode": "Weigh scale", "obs": ["7.1", "7.0", "7.2"], "status": "Accepted"},
        ]},
    "YF-4021": {"supplier": "Sunflag Iron & Steel", "date": "2026-06-15", "material": "EN8D bar Ø55",
        "params": [
            {"param": "Bar diameter", "spec": "Ø55±0.5 mm", "mode": "Vernier", "obs": ["55.1", "54.9", "55.0"], "status": "Accepted"},
            {"param": "Chemistry (C%)", "spec": "0.35-0.45", "mode": "Mill TC", "obs": ["0.41", "0.40", "0.42"], "status": "Accepted"},
            {"param": "Surface (seams/cracks)", "spec": "Nil", "mode": "MPI", "obs": ["OK", "OK", "Seam"], "status": "Rejected"},
        ]},
    "CE21609": {"supplier": "Mukand Ltd.", "date": "2026-06-10", "material": "SAE8620 bar Ø30/32",
        "params": [
            {"param": "Diameter", "spec": "Ø30/32 mm", "mode": "Vernier", "obs": ["31.0", "31.1", "30.9"], "status": "Accepted"},
            {"param": "Grain size", "spec": "5-8 (E112)", "mode": "Microscope", "obs": ["6", "7", "6"], "status": "Accepted"},
            {"param": "Decarb layer", "spec": "1% of dia max", "mode": "Microscope", "obs": ["0.2", "0.25", "0.3"], "status": "Accepted"},
        ]},
}

# In-process inspection (measured observations against spec — feeds out-of-spec detection)
INPROCESS = {
    "S-10254-5": {"op_no": 20, "date": "2026-06-20", "machine": "PDC 80T",
        "params": [
            {"param": "Weight", "spec": "101 gm", "mode": "WS", "first": "101.2", "obs": ["101.0", "100.8", "97.9", "101.1", "100.9"], "last": "101.0"},
            {"param": "DIM1", "spec": "134±0.2", "mode": "VC", "first": "134.0", "obs": ["134.1", "133.9", "134.0", "134.2", "134.05"], "last": "134.0"},
            {"param": "DIM7 Boss height", "spec": "63.6±0.1", "mode": "VC", "first": "63.6", "obs": ["63.62", "63.58", "63.6", "63.71", "63.6"], "last": "63.6"},
        ]},
    "YF-4021": {"op_no": 40, "date": "2026-06-24", "machine": "CNC Lathe",
        "params": [
            {"param": "Spigot dia", "spec": "Ø80.00-79.95", "mode": "Air gauge", "first": "79.98", "obs": ["79.97", "79.96", "80.02", "79.98", "79.99"], "last": "79.97"},
            {"param": "Flange thickness", "spec": "18±0.1", "mode": "VC", "first": "18.0", "obs": ["18.02", "17.98", "18.0", "18.05", "18.01"], "last": "18.0"},
        ]},
}

# PDIR — pre-dispatch inspection
PDIR = {
    "S-10254-5": {"date": "2026-06-28", "invoice": "SI/0641 / 28.06.2026", "qty": 500,
        "chars": [
            {"char": "Weight", "spec": "101 gm", "mode": "WS", "obs": ["101.0", "100.9", "101.1", "100.8", "101.0"]},
            {"char": "DIM1", "spec": "134±0.2", "mode": "VC", "obs": ["134.0", "134.1", "133.9", "134.0", "134.05"]},
            {"char": "Leak test", "spec": "No leak @2 bar", "mode": "Leak tester", "obs": ["OK", "OK", "OK", "OK", "OK"]},
        ], "status": "Accepted"},
    "YF-4021": {"date": "2026-07-01", "invoice": "SI/0655 / 01.07.2026", "qty": 300,
        "chars": [
            {"char": "Spigot dia", "spec": "Ø80.00-79.95", "mode": "Air gauge", "obs": ["79.97", "79.98", "79.96", "79.97", "79.99"]},
            {"char": "Spline", "spec": "Ø32H7", "mode": "Ring gauge", "obs": ["GO", "GO", "GO", "GO", "GO"]},
            {"char": "PCD", "spec": "Ø100±0.1", "mode": "CMM", "obs": ["100.02", "99.98", "100.0", "100.05", "99.97"]},
        ], "status": "Accepted"},
}

# NCR / CAR — non-conformance & corrective action log
NCRS = [
    {"part_no": "S-10254-5", "sl": 1, "month": "June 2026", "part": "Base", "act_qty": 5200,
     "inprocess_rej": 210, "pdi_rej": 18, "rej_pct": 4.4,
     "reason": "Porosity / leak at boss (Op 70 leak test)", "corrective_action": "Degassing cycle revised at Op 10; see 8D NCR-BASE-014", "status": "Open"},
    {"part_no": "S-10254-5", "sl": 2, "month": "June 2026", "part": "Base", "act_qty": 5200,
     "inprocess_rej": 95, "pdi_rej": 3, "rej_pct": 1.9,
     "reason": "Short shot / low weight (Op 20)", "corrective_action": "Injection pressure interlock added", "status": "Closed"},
    {"part_no": "YF-4021", "sl": 1, "month": "June 2026", "part": "Yoke Flange", "act_qty": 3100,
     "inprocess_rej": 74, "pdi_rej": 6, "rej_pct": 2.6,
     "reason": "Spigot dia oversize (Op 40) — tool wear", "corrective_action": "Tool-life count reduced; SPC tightened; see 8D NCR-YF-007", "status": "Open"},
    {"part_no": "CE21609", "sl": 1, "month": "June 2026", "part": "Pinion Shaft", "act_qty": 8000,
     "inprocess_rej": 120, "pdi_rej": 9, "rej_pct": 1.6,
     "reason": "Bore honing size variation (Op 80)", "corrective_action": "Honing stick dressing frequency revised", "status": "Closed"},
]

# 8D CAPA — root-cause / corrective-action reports (linked to NCRs)
CAPAS = [
    {"part_no": "S-10254-5", "notification_no": "NCR-BASE-014", "date": "2026-06-22", "part_name": "Base",
     "customer": "Four Front Pvt. Ltd.",
     "team": ["QA Engineer (lead)", "PDC Supervisor", "Maintenance", "Foundry Metallurgist"],
     "problem": {"what": "Coolant/oil leak from boss in customer assembly",
                 "why": "Sub-surface gas porosity connects to machined boss face",
                 "when": "June 2026 lots", "where": "Op 70 leak test + customer line", "who": "Assembly at customer",
                 "how": "Detected by 2-bar leak test", "how_many": "18 parts at PDI, 4 field returns"},
     "containment": "100% leak test; segregate June lots; sort at customer",
     "root_cause": "Inadequate degassing at melting (Op 10) → hydrogen porosity; die temperature low at Op 20 aggravating cold-shut near boss",
     "corrective_action": "Rotary degasser cycle time fixed to 10 min with timer interlock; die pre-heat + pyrometer interlock at Op 20",
     "preventive_action": "Add degassing time & die temp to the reaction plan and control plan; link leak rejects to melt records",
     "status": "In Progress"},
    {"part_no": "YF-4021", "notification_no": "NCR-YF-007", "date": "2026-06-26", "part_name": "Yoke Flange",
     "customer": "Tata Motors Ltd.",
     "team": ["QA Engineer (lead)", "CNC Setter", "Tooling", "Production"],
     "problem": {"what": "Spigot diameter oversize beyond Ø80.00", "why": "Insert wear not detected in time",
                 "when": "June 2026", "where": "Op 40 CNC turning", "who": "Machining", "how": "Air gauge, SPC drift",
                 "how_many": "74 in-process, 6 at PDI"},
     "containment": "100% air-gauge sorting; recall suspect bin",
     "root_cause": "Tool-life count set too high; no in-cycle offset compensation → gradual oversize",
     "corrective_action": "Reduce tool-life count by 20%; introduce automatic offset compensation; tighten SPC limits",
     "preventive_action": "Apply tool-life review to all turning operations; add trend alarm",
     "status": "In Progress"},
]

PARTS = {"S-10254-5": BASE, "YF-4021": YOKE}
