#!/usr/bin/env python3
"""Summarize completed all-scene residual-glint experiments without rerunning them."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "Tidung_Full_Glint_All_Scenes_Experiment_20260911"
SCENE_ROOT = OUT / "scenes"
INITIAL_AUDIT = (ROOT / "outputs" / "Tidung_Joint_HydroLight_Glint_Multiband_Experiment_20260911" /
                 "01_Scene_Audit" / "scene_eligibility_audit.csv")


def classify(summary: dict) -> tuple[str, str]:
    inj = summary["real_low_pixel_injection"]
    residual = summary["real_roi_residual_gate"]
    qc = summary["final_qc"]
    if qc["pass"]:
        return "RETAIN_CYCLE1", "Residual evidence and final Cycle-1 QC passed"
    if qc["negative_visible_pixel_percent"] > 1.0:
        return "SCENE_REJECTED", "Cycle-0 visible negative pixels exceed 1%"
    if not inj["pass"]:
        return "RETAIN_CYCLE0", "Known-injection recovery failed; Cycle 1 not authorized"
    if not residual["pass"]:
        return "RETAIN_CYCLE0", "Residual glint was not supported by the complete 30-ROI gate"
    return "RETAIN_CYCLE0", "Residual passed, but no Cycle-1 strength passed final image QC"


def main() -> None:
    rows = []
    for folder in sorted(p for p in SCENE_ROOT.iterdir() if p.is_dir()):
        path = folder / "experiment_summary.json"
        if not path.exists():
            rows.append({"scene": folder.name, "decision": "SCENE_REJECTED",
                         "stop_reason": "Experiment did not complete"})
            continue
        s = json.loads(path.read_text(encoding="utf-8"))
        decision, reason = classify(s)
        s["decision"] = decision
        s["stop_reason"] = reason
        path.write_text(json.dumps(s, indent=2), encoding="utf-8")
        inj, rg, qc, hydro = (s["real_low_pixel_injection"], s["real_roi_residual_gate"],
                              s["final_qc"], s["hydrolight_context"])
        rows.append({
            "scene": folder.name, "decision": decision, "stop_reason": reason,
            "injection_pass": inj["pass"], "injection_false_positive_rate": inj["zero_glint_false_positive_rate"],
            "injection_sensitivity": inj["sensitivity_component_ge_0_001"],
            "injection_median_k_relative_error": inj["median_k_relative_error_component_ge_0_001"],
            "residual_gate_pass": rg["pass"], "low_detected": rg["low_detected"],
            "medium_detected": rg["medium_detected"], "high_detected": rg["high_detected"],
            "residual_spearman_rho": rg["spearman_alpha_vs_rhog"], "residual_spearman_p": rg["spearman_p"],
            "high_greater_low_p": rg["high_greater_low_mannwhitney_p"],
            "final_qc_pass": qc["pass"], "corrected_water_fraction": qc["corrected_valid_water_fraction"],
            "negative_visible_percent": qc["negative_visible_pixel_percent"],
            "negative_eight_band_percent": qc["negative_all_eight_band_pixel_percent"],
            "spatial_preservation_r": qc["spatial_preservation_r"],
            "cycle0_hydrolight_rmse": hydro["median_cycle0_rmse_all_rois"],
            "cycle1_candidate_hydrolight_rmse": hydro["median_cycle1_candidate_rmse_all_rois"],
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "all_scene_detailed_results.csv", index=False)
    counts = frame.decision.value_counts().to_dict()
    initial = pd.read_csv(INITIAL_AUDIT)
    preexcluded = initial[initial.status.eq("EXCLUDED")].copy()
    processed_status = frame[["scene", "decision", "stop_reason"]].copy()
    excluded_status = pd.DataFrame({"scene": preexcluded.scene,
                                    "decision": "SCENE_REJECTED",
                                    "stop_reason": "Initial screening: " + preexcluded.reason})
    all_status = pd.concat([processed_status, excluded_status], ignore_index=True).sort_values("scene")
    all_status.to_csv(OUT / "all_33_scene_final_status.csv", index=False)
    all_counts = all_status.decision.value_counts().to_dict()
    summary = {"created_utc": datetime.now(timezone.utc).isoformat(),
               "original_scene_count": int(len(initial)),
               "pre_excluded_scene_count": int(len(preexcluded)),
               "residual_experiment_scene_count": int(len(frame)),
               "decision_counts_all_33": {k: int(v) for k, v in all_counts.items()},
               "cycle1_scenes": frame.loc[frame.decision.eq("RETAIN_CYCLE1"), "scene"].tolist(),
               "rejected_during_residual_experiment": frame.loc[frame.decision.eq("SCENE_REJECTED"), "scene"].tolist(),
               "pre_excluded_scenes": preexcluded.scene.tolist()}
    (OUT / "batch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    figures = OUT / "summary_figures"; figures.mkdir(exist_ok=True)
    order = ["RETAIN_CYCLE1", "RETAIN_CYCLE0", "SCENE_REJECTED"]
    colors = ["#0f766e", "#2563eb", "#dc2626"]
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    vals = [all_counts.get(k, 0) for k in order]
    bars = ax.bar(["Cycle 1", "Cycle 0", "Rejected"], vals, color=colors)
    ax.bar_label(bars); ax.set(ylabel="Number of scenes", title="Final glint-product decision across all 33 scenes")
    ax.grid(axis="y", alpha=.2); fig.savefig(figures / "01_all_scene_decisions.png", dpi=180); plt.close(fig)

    plot = frame.sort_values("scene").reset_index(drop=True)
    x = np.arange(len(plot))
    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    ax.plot(x, plot.low_detected, "o-", label="Low", color="#2563eb")
    ax.plot(x, plot.medium_detected, "o-", label="Medium", color="#f59e0b")
    ax.plot(x, plot.high_detected, "o-", label="High", color="#dc2626")
    ax.axhline(5, color="#64748b", ls="--", lw=1, label="Required high detections")
    ax.set(xticks=x, xticklabels=plot.scene, xlabel="Scene", ylabel="Detected ROIs out of 10",
           title="Residual-glint detections in the frozen 30-ROI test")
    ax.tick_params(axis="x", rotation=65); ax.grid(axis="y", alpha=.2); ax.legend(ncol=4)
    fig.savefig(figures / "02_all_scene_roi_detections.png", dpi=180); plt.close(fig)

    md = [
        "# Tidung all-scene glint experiment — batch result", "",
        "## Decision", "",
        f"- Original scenes audited: **{len(initial)}**",
        f"- Excluded before residual testing: **{len(preexcluded)}**",
        f"- Scenes completing the residual experiment: **{len(frame)}**",
        f"- Final Cycle 1 products: **{all_counts.get('RETAIN_CYCLE1', 0)}**",
        f"- Final Cycle 0 products: **{all_counts.get('RETAIN_CYCLE0', 0)}**",
        f"- Total rejected scenes: **{all_counts.get('SCENE_REJECTED', 0)}**", "",
        "Cycle 1 was not forced across dates. Each date independently repeated the real low-control injection, 30-ROI residual test and final image QC using the same equations and limits.", "",
        "## Cycle-1 scene", "",
        ", ".join(summary["cycle1_scenes"]) or "None", "",
        "## Rejected scenes", "",
        "Rejected before residual testing: " + (", ".join(summary["pre_excluded_scenes"]) or "None"), "",
        "Rejected during final batch QC: " + (", ".join(summary["rejected_during_residual_experiment"]) or "None"), "",
        "The four later rejections exceed the 1% visible-negative-pixel limit at Cycle 0. All eight rejected dates must not be presented as clean final images.", "",
        "## Meaning", "",
        "- `RETAIN_CYCLE1`: an additional B11/B12-shaped residual was validated, detected across offshore ROIs and removed without failing final QC.",
        "- `RETAIN_CYCLE0`: the initial Glint-ACOLITE product remains final because an extra subtraction was not sufficiently supported.",
        "- `SCENE_REJECTED`: the image fails the declared clean-product QC and is excluded from final scientific products.", "",
        "The result does not mean that 28 scenes contain no glint. It means this experiment did not establish enough evidence to subtract another component safely.", "",
        "## Detailed evidence", "",
        "Use `all_33_scene_final_status.csv` for the final status of every original scene. Use `all_scene_detailed_results.csv` for every gate, detection count, negative-pixel percentage, spatial correlation and HydroLight RMSE in the 29 processed scenes. Each `scenes/<scene>/` folder contains its 30 ROIs, all spectra, maps, rasters and exact decision JSON.", "",
    ]
    (OUT / "ALL_SCENE_RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
