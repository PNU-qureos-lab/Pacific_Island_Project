#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cfg_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.json")
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
required = ["comparison_outputs", "joint_multiband_outputs", "controlled_hydrolight_outputs", "experiment_output", "l2a_archive", "final_product_output", "scene"]
failed = False
for key in required:
    if key not in cfg:
        print(f"MISSING KEY  {key}"); failed = True; continue
    if key in {"scene"}:
        print(f"VALUE        {key}: {cfg[key]}"); continue
    p = Path(cfg[key]).expanduser()
    if not p.is_absolute(): p = (ROOT / p).resolve()
    status = "OK" if p.exists() or key in {"experiment_output", "final_product_output"} else "MISSING"
    print(f"{status:12} {key}: {p}")
    failed |= status == "MISSING"
raise SystemExit(1 if failed else 0)
