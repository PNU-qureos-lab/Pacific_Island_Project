#!/usr/bin/env python3
"""Run the frozen full residual-glint experiment over all retained Tidung scenes."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_tidung_full_residual_glint_experiment as experiment


JOINT = ROOT / "outputs" / "Tidung_Joint_HydroLight_Glint_Multiband_Experiment_20260911"
OUT = ROOT / "outputs" / "Tidung_Full_Glint_All_Scenes_Experiment_20260911"
SCENES = sorted(p.name for p in (JOINT / "02_Multiband_Inputs").iterdir() if p.is_dir())


def write_progress(rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "batch_progress.csv", index=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for number, scene in enumerate(SCENES, 1):
        scene_out = OUT / "scenes" / scene
        experiment.SCENE = scene
        experiment.OUT = scene_out
        experiment.RNG = np.random.default_rng(20260911 + int(scene[:8]))
        print(f"[{number:02d}/{len(SCENES):02d}] {scene} RUNNING", flush=True)
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                experiment.main()
            summary = json.loads((scene_out / "experiment_summary.json").read_text(encoding="utf-8"))
            row = {
                "scene": scene,
                "status": "COMPLETE",
                "decision": summary["decision"],
                "injection_pass": summary["real_low_pixel_injection"]["pass"],
                "residual_gate_pass": summary["real_roi_residual_gate"]["pass"],
                "final_qc_pass": summary["final_qc"]["pass"],
                "low_detected": summary["real_roi_residual_gate"]["low_detected"],
                "medium_detected": summary["real_roi_residual_gate"]["medium_detected"],
                "high_detected": summary["real_roi_residual_gate"]["high_detected"],
                "corrected_water_fraction": summary["final_qc"]["corrected_valid_water_fraction"],
                "negative_visible_percent": summary["final_qc"]["negative_visible_pixel_percent"],
                "negative_eight_band_percent": summary["final_qc"]["negative_all_eight_band_pixel_percent"],
                "spatial_preservation_r": summary["final_qc"]["spatial_preservation_r"],
                "cycle0_hydrolight_rmse": summary["hydrolight_context"]["median_cycle0_rmse_all_rois"],
                "final_candidate_hydrolight_rmse": summary["hydrolight_context"]["median_cycle1_candidate_rmse_all_rois"],
                "error": "",
            }
            print(f"[{number:02d}/{len(SCENES):02d}] {scene} {row['decision']}", flush=True)
        except Exception as exc:
            scene_out.mkdir(parents=True, exist_ok=True)
            (scene_out / "FAILED.txt").write_text(traceback.format_exc(), encoding="utf-8")
            row = {"scene": scene, "status": "FAILED", "decision": "SCENE_REJECTED",
                   "injection_pass": False, "residual_gate_pass": False,
                   "final_qc_pass": False, "error": str(exc)}
            print(f"[{number:02d}/{len(SCENES):02d}] {scene} FAILED: {exc}", flush=True)
        (scene_out / "run_log.txt").write_text(captured.getvalue(), encoding="utf-8")
        rows.append(row)
        write_progress(rows)

    frame = pd.DataFrame(rows)
    counts = frame.decision.value_counts(dropna=False).to_dict()
    batch = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scene_count": len(SCENES),
        "completed": int((frame.status == "COMPLETE").sum()),
        "failed": int((frame.status == "FAILED").sum()),
        "decision_counts": {str(k): int(v) for k, v in counts.items()},
        "method": "Frozen one-cycle residual-glint workflow validated on 20240925_S2A",
    }
    (OUT / "batch_summary.json").write_text(json.dumps(batch, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), OUT / Path(__file__).name)
    shutil.copy2(ROOT / "scripts" / "run_tidung_full_residual_glint_experiment.py",
                 OUT / "run_tidung_full_residual_glint_experiment.py")
    print(json.dumps(batch, indent=2), flush=True)


if __name__ == "__main__":
    main()
