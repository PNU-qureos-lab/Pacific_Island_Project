#!/usr/bin/env python
"""Build the local multi-scene Tidung final-products HTML report."""

from __future__ import annotations

import csv
import html as html_lib
import json
import math
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio


PROJECT = Path(r"C:\Users\phili\Documents\ChatGPT\ACOLITE-Glint Correction")
ROOT = Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
SOURCE = PROJECT / "outputs" / "Tidung_Full_Glint_All_Scenes_Experiment_20260911"
JOINT = PROJECT / "outputs" / "Tidung_Joint_HydroLight_Glint_Multiband_Experiment_20260911"
ASSETS = ROOT / "report-assets"
BANDS = ("B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A")
WAVE = (492, 560, 665, 704, 740, 783, 833, 865)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        return ds.read(1).astype(float), {"bounds": list(ds.bounds), "crs": str(ds.crs)}


def robust_limits(arrays: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    lows, highs = [], []
    for channel in range(3):
        values = np.concatenate([a[channel][np.isfinite(a[channel])] for a in arrays])
        lows.append(float(np.percentile(values, 1)))
        highs.append(float(np.percentile(values, 99.5)))
    return np.array(lows), np.array(highs)


def save_rgb(path: Path, rgb: np.ndarray, low: np.ndarray, high: np.ndarray) -> None:
    shown = np.moveaxis(rgb, 0, -1)
    valid = np.all(np.isfinite(shown), axis=2)
    scaled = np.clip((shown - low) / np.maximum(high - low, 1e-6), 0, 1)
    scaled = np.power(scaled, 0.85)
    rgba = np.zeros((*valid.shape, 4), dtype=np.uint8)
    rgba[..., :3] = np.round(scaled * 255).astype(np.uint8)
    rgba[..., 3] = valid.astype(np.uint8) * 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def roi_final_spectra(scene: str, roi_rows: list[dict]) -> list[list[float | None]]:
    stacks = []
    for band in BANDS:
        p = ROOT / "FINAL_PRODUCTS" / scene / "01_Final_BOA_Reflectance" / f"{scene}_{band}_final_BOA_reflectance.tif"
        a, _ = read_band(p)
        stacks.append(a)
    data = np.stack(stacks)
    answer = []
    for r in roi_rows:
        y, x = int(float(r["row"])), int(float(r["col"]))
        window = data[:, max(0, y-3):y+4, max(0, x-3):x+4]
        answer.append([float(np.nanmedian(window[i])) if np.isfinite(window[i]).any() else None for i in range(8)])
    return answer


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def save_median_fit_figures(csv_path: Path, out_dir: Path, mode: str = "fit", cycle1_retained: bool = False) -> list[Path]:
    """Create scalable one-panel median SVGs without individual ROI lines."""
    fit_rows = rows(csv_path)
    all_values = []
    prefixes = ("cycle0", "candidate", "water") if mode == "fit" else ("before", "cycle0")
    for row in fit_rows:
        for prefix in prefixes:
            all_values.extend(float(row[f"{prefix}_{band}"]) for band in BANDS)
    ymin, ymax = float(np.nanmin(all_values)), float(np.nanmax(all_values))
    pad = max((ymax - ymin) * 0.08, 0.001)
    paths = []
    for group in ("LOW", "MEDIUM", "HIGH"):
        group_rows = [row for row in fit_rows if row["stratum"] == group]
        medians = {}
        for prefix in prefixes:
            medians[prefix] = [float(np.median([float(row[f"{prefix}_{band}"]) for row in group_rows])) for band in BANDS]
        width, height = 1050, 620
        left, right, top, bottom = 105, 35, 120, 85
        x0, x1 = left, width - right
        y0, y1 = top, height - bottom
        lo, hi = ymin - pad, ymax + pad
        xs = [x0 + (float(w) - WAVE[0]) / (WAVE[-1] - WAVE[0]) * (x1 - x0) for w in WAVE]
        def ys(values):
            return [y1 - (float(v) - lo) / (hi - lo) * (y1 - y0) for v in values]
        def series(values, color, dashed=False, square=False):
            yy = ys(values)
            dash = ' stroke-dasharray="12 8"' if dashed else ''
            line = f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in zip(xs,yy))}" fill="none" stroke="{color}" stroke-width="5"{dash}/>'
            marker = ''.join((f'<rect x="{x-6:.1f}" y="{y-6:.1f}" width="12" height="12" fill="{color}"/>' if square else f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>') for x,y in zip(xs,yy))
            return line + marker
        grid = []
        for tick in range(6):
            y = y1 - tick / 5 * (y1 - y0)
            value = lo + tick / 5 * (hi - lo)
            grid.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#dbe3ea"/><text x="{x0-12}" y="{y+6:.1f}" text-anchor="end" font-size="16">{value:.3f}</text>')
        labels = ''.join(f'<text x="{x:.1f}" y="{y1+30}" text-anchor="middle" font-size="15">{int(w)}</text>' for x,w in zip(xs,WAVE))
        if mode == "fit":
            if cycle1_retained:
                legend_svg = '<line x1="125" y1="72" x2="170" y2="72" stroke="#0f766e" stroke-width="6"/><text x="180" y="79" font-size="17">Cycle 0</text><line x1="315" y1="72" x2="360" y2="72" stroke="#2563eb" stroke-width="6"/><text x="370" y="79" font-size="17">Final Cycle 1 (retained)</text><line x1="585" y1="72" x2="630" y2="72" stroke="#d97706" stroke-width="6" stroke-dasharray="12 8"/><text x="640" y="79" font-size="17">Selected possible HydroLight water</text>'
                # Draw Cycle 0 last so it remains visible even where the curves overlap.
                series_svg = series(medians['water'],'#d97706',True,True) + series(medians['candidate'],'#2563eb') + series(medians['cycle0'],'#0f766e')
            else:
                legend_svg = '<line x1="245" y1="72" x2="290" y2="72" stroke="#0f766e" stroke-width="6"/><text x="300" y="79" font-size="17">Final retained product: Cycle 0</text><line x1="620" y1="72" x2="665" y2="72" stroke="#d97706" stroke-width="6" stroke-dasharray="12 8"/><text x="675" y="79" font-size="17">Selected possible HydroLight water</text>'
                # A rejected Cycle-1 candidate is intentionally omitted from the result graph.
                series_svg = series(medians['water'],'#d97706',True,True) + series(medians['cycle0'],'#0f766e')
            stem = "median_fit"
        else:
            legend_svg = '<line x1="280" y1="72" x2="325" y2="72" stroke="#334155" stroke-width="6"/><text x="335" y="79" font-size="17">Original L2A before correction</text><line x1="585" y1="72" x2="630" y2="72" stroke="#0f766e" stroke-width="6"/><text x="640" y="79" font-size="17">Cycle 0 after first correction</text>'
            series_svg = series(medians['before'],'#334155') + series(medians['cycle0'],'#0f766e')
            stem = "median_before_cycle0"
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/><text x="{width/2}" y="38" text-anchor="middle" font-size="27" font-weight="700">{group}: median of 10 offshore ROIs</text>{legend_svg}{''.join(grid)}<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#111" stroke-width="2"/><line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#111" stroke-width="2"/>{labels}{series_svg}<text x="{width/2}" y="{height-25}" text-anchor="middle" font-size="20">Wavelength (nm)</text><text x="28" y="{(y0+y1)/2}" text-anchor="middle" font-size="20" transform="rotate(-90 28 {(y0+y1)/2})">BOA reflectance</text></svg>'''
        path = out_dir / f"{stem}_{group}.svg"
        path.write_text(svg, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    concept_source = Path(r"C:\Users\phili\Downloads\glint-concept-v6.html")
    concept_assets = Path(r"C:\Users\phili\Downloads\glint-concept-v6-assets")
    concept_out = ROOT / "concept"
    concept_out.mkdir(parents=True, exist_ok=True)
    if concept_assets.exists():
        shutil.copytree(concept_assets, concept_out / "glint-concept-v6-assets", dirs_exist_ok=True)
    decisions = rows(ROOT / "00_MASTER_QC" / "retained_scene_downstream_QC.csv")
    scene_data = []
    for decision in decisions:
        scene = decision["scene"]
        summary = json.loads((SOURCE / "scenes" / scene / "experiment_summary.json").read_text(encoding="utf-8"))
        roi = rows(SOURCE / "scenes" / scene / "01_Inputs" / "selected_30_offshore_rois.csv")
        before = []
        cycle0 = []
        final = []
        for band in ("B04", "B03", "B02"):
            a, geo = read_band(JOINT / "02_Multiband_Inputs" / scene / f"{band}_BOA_20m.tif")
            before.append(a)
            a, _ = read_band(JOINT / "03_Glint_ACOLITE_Cycle0" / scene / f"Cycle0_{band}.tif")
            cycle0.append(a)
            if summary["final_qc"]["retained_product"] == "Cycle0":
                final.append(a.copy())
            else:
                a, _ = read_band(ROOT / "FINAL_PRODUCTS" / scene / "01_Final_BOA_Reflectance" / f"{scene}_{band}_final_BOA_reflectance.tif")
                final.append(a)
        rgb_sets = [np.stack(before), np.stack(cycle0), np.stack(final)]
        low, high = robust_limits(rgb_sets)
        images = {}
        for label, arr in zip(("before", "cycle0", "final"), rgb_sets):
            p = ASSETS / scene / f"{label}_same_water_stretch.png"
            save_rgb(p, arr, low, high)
            images[label] = rel(p)

        figure_source = SOURCE / "scenes" / scene / "13_Figures"
        figure_names = {
            "roi_map": "02_roi_map.png",
            "known": "03_real_pixel_injection_recovery.png",
            "before_cycle0": "04_all_roi_before_cycle0.png",
            "residual": "05_real_roi_residual_evidence.png",
            "fit": "07_all_roi_cycle0_cycle1_hydrolight.png",
            "spatial": "09_cycle1_spatial_products.png",
        }
        figures = {}
        for key, name in figure_names.items():
            src = figure_source / name
            if src.exists():
                dst = ASSETS / scene / name
                shutil.copy2(src, dst)
                figures[key] = rel(dst)
                if key in {"known", "before_cycle0", "fit"}:
                    with Image.open(src) as composite:
                        panel_paths = []
                        for panel_index in range(3):
                            left = round(composite.width * panel_index / 3)
                            right = round(composite.width * (panel_index + 1) / 3)
                            crop = composite.crop((left, 0, right, composite.height))
                            panel_path = ASSETS / scene / f"{src.stem}_panel_{panel_index + 1}.png"
                            crop.save(panel_path, optimize=True)
                            panel_paths.append(rel(panel_path))
                        figures[f"{key}_panels"] = panel_paths
        retest_src = SOURCE / "scenes" / scene / "09_Final_Residual_Retest" / "final_residual_retest.png"
        if retest_src.exists():
            retest_dst = ASSETS / scene / "10_final_residual_retest.png"
            shutil.copy2(retest_src, retest_dst)
            figures["retest"] = rel(retest_dst)
        roi_csv = SOURCE / "scenes" / scene / "01_Inputs" / "selected_30_offshore_rois.csv"
        if roi_csv.exists():
            figures["before_cycle0_median_panels"] = [
                rel(p) for p in save_median_fit_figures(roi_csv, ASSETS / scene, mode="before")
            ]
        fit_csv = SOURCE / "scenes" / scene / "05_ROI_Residual_Test" / "all_30_roi_residual_fits.csv"
        if fit_csv.exists():
            figures["fit_median_panels"] = [
                rel(p) for p in save_median_fit_figures(
                    fit_csv,
                    ASSETS / scene,
                    cycle1_retained=decision["additional_residual_correction_applied"] == "True",
                )
            ]

        # If Cycle 0 is retained, the final spectral result is definitionally
        # identical to Cycle 0.  Reuse the same ROI values so the report cannot
        # introduce artificial differences through a second sampling path.
        if summary["final_qc"]["retained_product"] == "Cycle0":
            final_spectra = [[float(r[f"cycle0_{b}"]) for b in BANDS] for r in roi]
        else:
            final_spectra = roi_final_spectra(scene, roi)
        swir_dir = PROJECT / "outputs" / "Tidung_Glint_Comparison_Rerun_20260903" / "06_ACOLITE" / "SWIR_Selection" / scene
        b11_candidate, _ = read_band(swir_dir / "B11_candidate_blue.tif")
        b12_candidate, _ = read_band(swir_dir / "B12_candidate_blue.tif")
        b11_selected, _ = read_band(swir_dir / "SWIR_selection_B11_is_1.tif")
        roi_payload = []
        for i, r in enumerate(roi):
            y, x = int(float(r["row"])), int(float(r["col"]))
            window = (slice(y - 3, y + 4), slice(x - 3, x + 4))
            c11 = float(np.nanmean(b11_candidate[window]))
            c12 = float(np.nanmean(b12_candidate[window]))
            use11 = float(np.nanmean(b11_selected[window]))
            roi_payload.append({
                "id": r["roi"], "group": r["stratum"],
                "rhog": float(r["rhog_ref_mean"]),
                "b11CandidateBlue": c11,
                "b12CandidateBlue": c12,
                "selectedSwir": "B11" if use11 >= 0.5 else "B12",
                "b11SelectedPercent": 100.0 * use11,
                "before": [float(r[f"before_{b}"]) for b in BANDS],
                "cycle0": [float(r[f"cycle0_{b}"]) for b in BANDS],
                "removed0": [float(r[f"glint0_{b}"]) for b in BANDS],
                "final": final_spectra[i],
            })
        qc_rows = rows(ROOT / "FINAL_PRODUCTS" / scene / "04_QC" / "band_value_and_conversion_QC.csv")
        band_qc = {r["band"]: r for r in qc_rows}
        final_retest_path = ROOT / "FINAL_PRODUCTS" / scene / "05_Provenance" / "final_residual_retest_summary.json"
        final_retest = json.loads(final_retest_path.read_text(encoding="utf-8")) if final_retest_path.exists() else None
        bounds = geo["bounds"]
        # Raster bounds are projected; all products share the fixed Tidung crop.
        lonlat_bounds = [[-5.825, 106.465], [-5.775, 106.540]]
        scene_data.append({
            "scene": scene,
            "retained": decision["retained_product"],
            "extra": decision["additional_residual_correction_applied"] == "True",
            "downstream": decision["provisional_downstream_eligibility"],
            "reason": summary["stop_reason"],
            "finalRetest": final_retest,
            "images": images, "bounds": lonlat_bounds,
            "figures": figures,
            "evidence": {
                "injectionPass": summary["real_roi_residual_gate"]["injection_validation_pass"],
                "detectedLow": summary["real_roi_residual_gate"]["low_detected"],
                "detectedMedium": summary["real_roi_residual_gate"]["medium_detected"],
                "detectedHigh": summary["real_roi_residual_gate"]["high_detected"],
                "highMinusLow": summary["real_roi_residual_gate"]["high_minus_low_median_component"],
                "correlation": summary["real_roi_residual_gate"]["spearman_alpha_vs_rhog"],
                "correlationP": summary["real_roi_residual_gate"]["spearman_p"],
                "highGreaterLowP": summary["real_roi_residual_gate"]["high_greater_low_mannwhitney_p"],
                "detectionLimit": summary["real_low_pixel_injection"]["detection_limit_reflectance"],
                "rmseImprovementLimit": summary["real_low_pixel_injection"]["minimum_real_rmse_improvement_reflectance"],
                "improvementGainLimit": summary["real_low_pixel_injection"]["minimum_injection_improvement_gain_percent"],
                "shapeSimilarityLimit": summary["real_low_pixel_injection"]["minimum_shape_similarity"],
                "zeroFalsePositiveRate": summary["real_low_pixel_injection"]["zero_glint_false_positive_rate"],
                "injectionSensitivity": summary["real_low_pixel_injection"]["sensitivity_component_ge_0_001"],
                "medianKRelativeError": summary["real_low_pixel_injection"]["median_k_relative_error_component_ge_0_001"],
                "medianRecoveryRmse": summary["real_low_pixel_injection"]["median_corrected_to_base_rmse"],
                "rmse0": summary["hydrolight_context"]["median_cycle0_rmse_all_rois"],
                "rmse1": summary["hydrolight_context"]["median_cycle1_candidate_rmse_all_rois"],
            },
            "roi": roi_payload,
            "qc": {
                "negative": float(decision["visible_negative_percent_max"]),
                "roundtrip": max(float(r["Rrs_rrs_roundtrip_max_abs_error"]) for r in qc_rows),
                "RrsB02": float(band_qc["B02"]["above_surface_Rrs_median_sr-1"]),
                "RrsB03": float(band_qc["B03"]["above_surface_Rrs_median_sr-1"]),
                "RrsB04": float(band_qc["B04"]["above_surface_Rrs_median_sr-1"]),
            },
            "downloads": {
                "boa": rel(ROOT / "FINAL_PRODUCTS" / scene / "01_Final_BOA_Reflectance"),
                "Rrs": rel(ROOT / "FINAL_PRODUCTS" / scene / "02_Rrs_Approx"),
                "rrs": rel(ROOT / "FINAL_PRODUCTS" / scene / "03_rrs_Approx"),
                "qc": rel(ROOT / "FINAL_PRODUCTS" / scene / "04_QC" / "band_value_and_conversion_QC.csv"),
            },
        })

    # Build a transparent 80-scene ledger by combining the original screening
    # inventory with the frozen 33-scene experiment decisions.
    screening_path = PROJECT / "outputs" / "Tidung_Glint_Comparison_Rerun_20260903" / "00_Scene_Selection" / "scene_inventory.csv"
    screening = rows(screening_path) if screening_path.exists() else []
    screening_by_scene = {f'{r["date"]}_{r["platform"]}': r for r in screening}
    status_rows = rows(SOURCE / "all_33_scene_final_status.csv")
    status_by_scene = {r["scene"]: r for r in status_rows}
    ledger = []
    for scene, screening_row in sorted(screening_by_scene.items()):
        status = status_by_scene.get(scene)
        if status:
            decision = status["decision"]
            category = {
                "RETAIN_CYCLE0": "Retained — Cycle 0",
                "RETAIN_CYCLE1": "Retained — Cycle 1",
                "SCENE_REJECTED": "Processed — rejected by final QC",
            }.get(decision, decision)
            reason = status["stop_reason"]
        elif screening_row["decision"] == "ACCEPT":
            category = "Eligible — not processed"
            reason = "Passed the initial water/cloud gate but was omitted from the frozen 33-scene experiment; it still requires processing."
        else:
            category = "Rejected at initial screening"
            reason = screening_row["decision_reason"]
        ledger.append({"scene": scene, "category": category, "reason": reason})
    # Open the report on the scientifically exceptional scene: the only scene
    # where the complete residual-glint gate authorized Cycle 1.
    scene_data.sort(key=lambda item: (not item["extra"], item["scene"]))
    payload = json.dumps({"bands": list(BANDS), "wavelengths": list(WAVE), "scenes": scene_data, "archive": ledger}, separators=(",", ":"))
    html = TEMPLATE.replace("__DATA__", payload)
    html = html.replace(
        '<p><b>Purpose:</b> quantify what the first correction removed and determine whether it produced unsafe negative water values.</p><svg',
        '<p><b>Interpretation:</b> this is the reflectance subtracted by Cycle 0. Larger HIGH values mean stronger subtraction at locations with larger original glint estimates. It does not measure what remains after correction.</p><svg',
        1,
    )
    html = html.replace('<h2>3. Cycle 0 response and safety evaluation</h2>', '<h2>Reflectance removed by Cycle 0</h2>')
    html = html.replace('<p><b>Purpose:</b> quantify what the first correction removed and determine whether it produced unsafe negative water values.</p>', '<p>This is original L2A minus Cycle 0. It shows the amount removed at each wavelength; it is not an after-correction spectrum.</p>')
    html = html.replace('Median reflectance removed by Cycle 0', 'Reflectance removed by Cycle 0')
    html = html.replace('<h2>4. Cycle 0 calculation</h2>', '<h2>2. Cycle 0 calculation</h2>')
    html = html.replace('<h2>6. HIGH–LOW separation</h2>', '<h2>Cycle 0 HIGH–LOW change</h2>')
    html = html.replace('<h2>8. Cycle 0 quality control</h2>', '<h2>4. Cycle 0 safety</h2>')
    html = html.replace("h+=cycle0Evaluation(s);h+=cycle0Qc(s);", "h+=cycle0Evaluation(s);")
    html = html.replace('Selected ROI values of ρg,ref (small to large)', 'Glint estimate used to classify each ROI')
    html = html.replace('Selected SWIR reference ρg,ref', 'Glint classification value')
    html = html.replace('Glint estimate used to classify each ROI', 'Mean SWIR surface-reflection reference for each 7 × 7 ROI')
    html = html.replace('Glint classification value', 'Mean SWIR reference from 49 valid water pixels')
    html = html.replace('<h2>1. Original glint check</h2>', '<h2>2. Original surface-reflection assessment</h2>')
    html = html.replace('<h2>2. Cycle 0 calculation</h2>', '<h2>3. Cycle 0 calculation</h2>')
    html = html.replace('<h2>3. Cycle 0 result</h2>', '<h2>4. Cycle 0 result</h2>')
    html = html.replace('<h2>5. HydroLight residual calculation</h2>', '<h2>5. HydroLight residual fitting</h2>')
    html = html.replace('<h2>6. Residual glint check</h2>', '<h2>6. Residual-glint check on Cycle 0</h2>')
    html = html.replace('<h2>Accepted scene: spectra at all three stages</h2>', '<h2>7. Cycle 1 correction and three-stage spectra</h2>')
    html = html.replace('<h2>Final repeated glint check: Cycle 0 versus Cycle 1</h2>', '<h2>8. Final repeated glint check</h2>')
    html = html.replace('<div class="card"><h2>8. Final repeated glint check</h2><table>', '<details class="card"><summary><b>Show complete Cycle 0 versus Cycle 1 numerical summary</b></summary><table>')
    html = html.replace('Processing therefore stopped at Cycle 1.</p></div>`:\'\'}', 'Processing therefore stopped at Cycle 1.</p></details>`:\'\'}')
    html = html.replace(
        "${roiRankingSvg(s)}${spectrumSvg(s,'before','Original L2A spectra')}<p><b>Interpretation:</b>",
        "${roiRankingSvg(s)}${spectrumSvg(s,'before','Original L2A spectra')}<div class=\"status\">${metric('LOW classification median',med('LOW').toFixed(6))}${metric('MEDIUM classification median',med('MEDIUM').toFixed(6))}${metric('HIGH classification median',med('HIGH').toFixed(6))}</div><p><b>Interpretation:</b>",
    )
    html = html.replace(
        "${roiRankingSvg(s)}${spectrumSvg(s,'before','Original L2A spectra')}",
        "${roiRankingSvg(s)}<p class=\"note\"><b>What these points are:</b> real values calculated from this Sentinel-2 scene. Each point is the mean selected SWIR surface-reflection reference from 49 valid pixels in one 7 × 7 offshore-water ROI. It is not field-measured glint, water depth, pure glint reflectance, or the visible-band amount removed. LOW, MEDIUM and HIGH are relative groups within this scene.</p>${spectrumSvg(s,'before','Original L2A spectra')}",
    )
    html = html.replace(
        "${metric('HIGH classification median',med('HIGH').toFixed(6))}</div><p><b>Interpretation:</b>",
        "${metric('HIGH classification median',med('HIGH').toFixed(6))}</div><table><tr><th>Original evidence</th><th>Value shown</th><th>Role</th></tr><tr><td>B11-derived estimates</td><td>${Math.min(...s.roi.map(r=>r.b11CandidateBlue)).toFixed(6)} to ${Math.max(...s.roi.map(r=>r.b11CandidateBlue)).toFixed(6)}</td><td>First SWIR-derived candidate</td></tr><tr><td>B12-derived estimates</td><td>${Math.min(...s.roi.map(r=>r.b12CandidateBlue)).toFixed(6)} to ${Math.max(...s.roi.map(r=>r.b12CandidateBlue)).toFixed(6)}</td><td>Second SWIR-derived candidate</td></tr><tr><td>Selected medians: LOW / MEDIUM / HIGH</td><td>${med('LOW').toFixed(6)} / ${med('MEDIUM').toFixed(6)} / ${med('HIGH').toFixed(6)}</td><td>Ranks the fixed groups</td></tr><tr><td>HIGH minus LOW</td><td>${(med('HIGH')-med('LOW')).toFixed(6)}</td><td>Numerical group separation</td></tr><tr><td>Spatial evidence</td><td>30-ROI map above</td><td>Shows where the selected locations occur</td></tr><tr><td>Visible spectral evidence</td><td>Original spectral graph above</td><td>Checks brightness ordering across wavelengths</td></tr></table><p><b>Interpretation:</b>",
    )
    html = html.replace(
        '<tr><td>Selected medians: LOW / MEDIUM / HIGH</td>',
        "<tr><td>Selected LOW range</td><td>${Math.min(...s.roi.filter(r=>r.group==='LOW').map(r=>r.rhog)).toFixed(6)} to ${Math.max(...s.roi.filter(r=>r.group==='LOW').map(r=>r.rhog)).toFixed(6)}</td><td>Range among the 10 displayed LOW ROIs</td></tr><tr><td>Selected MEDIUM range</td><td>${Math.min(...s.roi.filter(r=>r.group==='MEDIUM').map(r=>r.rhog)).toFixed(6)} to ${Math.max(...s.roi.filter(r=>r.group==='MEDIUM').map(r=>r.rhog)).toFixed(6)}</td><td>Range among the 10 displayed MEDIUM ROIs</td></tr><tr><td>Selected HIGH range</td><td>${Math.min(...s.roi.filter(r=>r.group==='HIGH').map(r=>r.rhog)).toFixed(6)} to ${Math.max(...s.roi.filter(r=>r.group==='HIGH').map(r=>r.rhog)).toFixed(6)}</td><td>Range among the 10 displayed HIGH ROIs</td></tr><tr><td>Selected medians: LOW / MEDIUM / HIGH</td>",
    )
    html = html.replace(
        'the original surface-reflection estimate varies from LOW to HIGH, so Cycle 0 was applied. The visible spectral separation is supporting evidence and may be weak.',
        'B11- and B12-derived estimates indicate possible surface reflection. The selected reference, ROI locations and visible spectra provide the displayed evidence for applying Cycle 0. The LOW–HIGH ordering alone is not independent proof of glint.',
    )
    html = html.replace('<details><summary><b>Glint estimates used for all ROIs</b></summary>', '<details open><summary><b>B11-derived, B12-derived and selected values for all 30 ROIs</b></summary>')
    html = re.sub(
        r"h\+=`<div class=\"card\"><h2>4\. Cycle 0 result</h2>.*?`\+evidencePanelSet\(s\.figures\.before_cycle0_median_panels,'Original and Cycle 0 spectra'.*?\);h\+=highLowSummary\(s\);",
        "h+=`<div class=\"card\"><h2>4. Cycle 0 result</h2><p>Choose group medians for a clear summary or all 10 ROIs to inspect every spectrum.</p></div>`+beforeComparison(s);h+=highLowSummary(s);",
        html,
        count=1,
    )
    html = html.replace(
        "if(s.extra){h+=evidenceFigure(s.figures.spatial,'7. Cycle 1 correction'",
        "if(s.extra){h+=`<div class=\"card\"><h2>Accepted scene: spectra at all three stages</h2><p>The same fixed ROI groups are shown before correction, after Cycle 0, and after the accepted Cycle 1.</p>${spectrumSvg(s,'before','Original L2A — before Cycle 0')}${spectrumSvg(s,'cycle0','After Cycle 0')}${spectrumSvg(s,'final','After Cycle 1 — final retained')}<p><b>Interpretation:</b> compare the numerical y-axis values at each wavelength. Cycle 0 is the first subtraction; Cycle 1 is the additional subtraction authorized by all residual-glint tests.</p><p class=\"note\"><b>Conclusion:</b> this scene continued to Cycle 1 because all six residual-glint conditions passed. The final repeated test then found no residual glint above the fixed detection criteria.</p></div>`+evidenceFigure(s.figures.spatial,'7. Cycle 1 correction'",
        2,
    )
    html = html.replace(
        "${spectrumSvg(s,'final','After Cycle 1 — final retained')}<p><b>Interpretation:</b>",
        "${spectrumSvg(s,'final','After Cycle 1 — final retained')}<details open><summary><b>Numerical group medians at all three stages</b></summary><table><tr><th>Band</th><th>Original LOW</th><th>Original MEDIUM</th><th>Original HIGH</th><th>Cycle 0 LOW</th><th>Cycle 0 MEDIUM</th><th>Cycle 0 HIGH</th><th>Cycle 1 LOW</th><th>Cycle 1 MEDIUM</th><th>Cycle 1 HIGH</th></tr>${DATA.bands.map((b,i)=>`<tr><td>${b}</td>${['before','cycle0','final'].flatMap(stage=>['LOW','MEDIUM','HIGH'].map(g=>`<td>${median(s.roi.filter(r=>r.group===g).map(r=>r[stage][i])).toFixed(6)}</td>`)).join('')}</tr>`).join('')}</table></details><p><b>Interpretation:</b>",
    )
    html = html.replace(
        "roiRows}</table></details></div>`;h+=cycle0Calculation(s);",
        "roiRows}</table></details></div>`;h=`<div class=\"card note\"><h2>Processing decision</h2><table><tr><th>Stage</th><th>Evidence</th><th>Decision</th></tr><tr><td>Original L2A</td><td>Original surface-reflection values and spectra are checked below.</td><td><b>Glint correction required → apply Cycle 0</b></td></tr><tr><td>After Cycle 0</td><td>Six residual-glint checks are evaluated together.</td><td><b>${s.extra?'All six passed → apply Cycle 1':'At least one failed → stop at Cycle 0'}</b></td></tr><tr><td>After Cycle 1</td><td>${s.extra?'The same frozen detector is applied again.':'Not applicable because Cycle 1 was not applied.'}</td><td><b>${s.extra?'No residual detections → stop at Cycle 1':'Final product is Cycle 0'}</b></td></tr></table></div>`+h;h+=cycle0Calculation(s);",
    )
    html = html.replace(
        "<p><b>Interpretation:</b> compare the numerical y-axis values at each wavelength.",
        "${s.finalRetest?`<div class=\"card\"><h2>Final repeated glint check: Cycle 0 versus Cycle 1</h2><table><tr><th>Check</th><th>After Cycle 0</th><th>After Cycle 1</th><th>Interpretation</th></tr><tr><td>Complete ROI detections</td><td>${s.finalRetest.evaluation.detected_roi_reduction}</td><td>${s.finalRetest.evaluation.remaining_detected_rois}</td><td>No ROI passed the complete detector after Cycle 1.</td></tr><tr><td>LOW / MEDIUM / HIGH detections</td><td>${s.finalRetest.after_acolite.low_detected} / ${s.finalRetest.after_acolite.medium_detected} / ${s.finalRetest.after_acolite.high_detected}</td><td>${s.finalRetest.after_additional_correction.low_detected} / ${s.finalRetest.after_additional_correction.medium_detected} / ${s.finalRetest.after_additional_correction.high_detected}</td><td>The former HIGH concentration disappeared.</td></tr><tr><td>Median fitted component: HIGH</td><td>${s.finalRetest.after_acolite.median_component_high.toFixed(6)}</td><td>${s.finalRetest.after_additional_correction.median_component_high.toFixed(6)}</td><td>Final HIGH value is below the fixed ${s.finalRetest.fixed_detection_thresholds.component_limit_reflectance.toFixed(6)} detection limit.</td></tr><tr><td>Relationship with original glint pattern</td><td>r ${s.finalRetest.after_acolite.spearman_component_vs_original_B11_B12.toFixed(3)}; p ${s.finalRetest.after_acolite.spearman_p.toFixed(6)}</td><td>r ${s.finalRetest.after_additional_correction.spearman_component_vs_original_B11_B12.toFixed(3)}; p ${s.finalRetest.after_additional_correction.spearman_p.toFixed(3)}</td><td>The final fitted values no longer follow the original glint pattern.</td></tr><tr><td>HIGH greater than LOW</td><td>p ${s.finalRetest.after_acolite.high_greater_than_low_p.toFixed(6)}</td><td>p ${s.finalRetest.after_additional_correction.high_greater_than_low_p.toFixed(3)}</td><td>The final HIGH-greater-than-LOW ordering is not supported.</td></tr><tr><td>Median HydroLight RMSE</td><td>${s.finalRetest.after_acolite.median_hydrolight_rmse.toFixed(6)}</td><td>${s.finalRetest.after_additional_correction.median_hydrolight_rmse.toFixed(6)}</td><td>The final spectrum remains within the evaluated model comparison.</td></tr></table><p class=\"note\"><b>Final conclusion:</b> residual glint was detected after Cycle 0, so Cycle 1 was applied. After Cycle 1, zero ROIs passed the same complete detector and the original spatial ordering disappeared. Processing therefore stopped at Cycle 1.</p></div>`:''}<p><b>Interpretation:</b> compare the numerical y-axis values at each wavelength.",
        1,
    )
    html = html.replace('<h2>Accepted scene: spectra at all three stages</h2>', '<h2>7. Cycle 1 correction and three-stage spectra</h2>')
    html = html.replace('<h2>Final repeated glint check: Cycle 0 versus Cycle 1</h2>', '<h2>8. Final repeated glint check</h2>')
    html = html.replace('<div class="card"><h2>8. Final repeated glint check</h2><table>', '<details class="card"><summary><b>Show complete Cycle 0 versus Cycle 1 numerical summary</b></summary><table>')
    html = html.replace('Processing therefore stopped at Cycle 1.</p></div>`:\'\'}', 'Processing therefore stopped at Cycle 1.</p></details>`:\'\'}')
    html = html.replace('<h2>5. HydroLight simulation and water–glint fitting</h2>', '<h2>9. HydroLight water comparison</h2>')
    html = html.replace('<h2>6. Closest possible water and the decision not to subtract more</h2>', '<h2>HydroLight fitted result</h2>')
    html = html.replace('<h2>6. Confirmed residual component and retained Cycle 1</h2>', '<h2>HydroLight fitted result</h2>')
    html = html.replace('<h2>10. Residual-glint detection limit</h2>', '<h2>Detection thresholds</h2>')
    html = html.replace('<h2>7. Cycle 1 acceptance decision</h2>', '<h2>Six residual-glint checks after Cycle 0</h2>')
    html = html.replace('<h2>Processing decision</h2>', '<h2>1. Scene and final decision</h2>')
    html = re.sub(r'<tr><td>Arithmetic check</td><td>\$\{r\.before\[i\].*?</td></tr>', '', html)
    html = html.replace('<p><b>Purpose:</b> protect brightness that could plausibly come from real water.', '<p><b>Interpretation:</b> HydroLight protects brightness that could plausibly come from real water.')
    html = html.replace('Whether it is sufficient is decided in Section 4.', 'Residual evidence is evaluated in Sections 9–12.')
    html = html.replace('This supports the Cycle 0 response, but Section 4 separately tests whether detectable residual glint remains.', 'This confirms the direction of the subtraction; Sections 9–12 separately test whether detectable residual glint remains.')
    html = html.replace('<b>How to read it:</b> after correction,', '<b>Interpretation:</b> after correction,')
    # This detailed page is embedded under the primary report's third tab.
    # Start directly at results and do not repeat the correction-idea interface.
    html = html.replace('<button class="tab active" data-tab="concept">Correction idea</button>', '')
    html = html.replace('<button class="tab" data-tab="results">Scene result</button>', '<button class="tab active" data-tab="results">Scene result</button>')
    # Present the complete result as one ordered scrolling report.  The former
    # result/evidence/spectra/product/archive sub-tabs are retained as sections,
    # not separate navigation destinations.
    for button in (
        '<button class="tab" data-tab="evidence">Residual-glint analysis</button>',
        '<button class="tab" data-tab="spectra">30 ROI spectra</button>',
        '<button class="tab" data-tab="products">Products & QC</button>',
        '<button class="tab" data-tab="archive">Archive decisions</button>',
    ):
        html = html.replace(button, '')
    html = html.replace('<nav><button class="tab active" data-tab="results">Scene result</button></nav>', '')
    html = re.sub(
        r'<section id="concept" class="panel active">.*?</section>\s*<section id="results" class="panel">',
        '<section id="results" class="panel active">',
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace('<section id="evidence" class="panel">', '<section id="evidence" class="panel active">')
    html = html.replace('<section id="spectra" class="panel">', '<section id="spectra" class="panel active">')
    html = html.replace('<section id="products" class="panel">', '<section id="products" class="panel active">')
    html = html.replace('<section id="archive" class="panel">', '<section id="archive" class="panel active">')
    html = html.replace('renderEvidence(s);drawChart()', 'orderedEvidence(s);drawChart()')
    html = html.replace('<h2>All 30 offshore ROI spectra</h2>', '<h2>9. Final spectral and numeric quality</h2>')
    html = html.replace('<option value="final" selected>Final retained</option>', '<option value="final" selected>Final retained BOA</option><option value="finalRrs">Final approximate Rrs</option>')
    html = html.replace('Use the control to compare original L2A, first correction, and final retained reflectance.', 'Use the control to compare original L2A, Cycle 0, final retained BOA, and final approximate Rrs.')
    html = html.replace('</svg></div><div class="card note"><b>How to read it:</b> after correction,', '</svg><details><summary><b>Final approximate Rrs group-median values</b></summary><div id="rrsTable"></div></details></div><div class="card note"><b>How to read it:</b> choose Final approximate Rrs to plot all 30 ROI spectra in sr⁻¹. Rrs is calculated as final BOA / π. It passed numerical conversion checks but is not field-validated water-leaving reflectance. After correction,')
    html = html.replace("function drawChart(){const svg=document.getElementById('chart'),s=DATA.scenes[current],stage=document.getElementById('stage').value,", "function drawChart(){const svg=document.getElementById('chart'),s=DATA.scenes[current],stage=document.getElementById('stage').value,isRrs=stage==='finalRrs',sourceStage=isRrs?'final':stage,")
    html = html.replace("const vals=s.roi.flatMap(r=>r[stage]).filter(Number.isFinite)", "const vals=s.roi.flatMap(r=>r[sourceStage].map(v=>isRrs?v/Math.PI:v)).filter(Number.isFinite)")
    html = html.replace("const pts=r[stage].map((y,i)=>`${X(DATA.wavelengths[i])},${Y(y)}`).join(' ')", "const pts=r[sourceStage].map((v,i)=>{const y=isRrs?v/Math.PI:v;return `${X(DATA.wavelengths[i])},${Y(y)}`}).join(' ')")
    html = html.replace("median(rs.map(r=>r[stage][i]))", "median(rs.map(r=>isRrs?r[sourceStage][i]/Math.PI:r[sourceStage][i]))")
    html = html.replace('font-weight="700">BOA reflectance</text>`;svg.setAttribute', 'font-weight="700">${isRrs?\'Approximate Rrs (sr⁻¹)\':\'BOA reflectance\'}</text>`;svg.setAttribute')
    html = html.replace("svg.innerHTML=z}", "svg.innerHTML=z;const groups=['LOW','MEDIUM','HIGH'];document.getElementById('rrsTable').innerHTML='<p>Values are medians of the 10 ROIs in each fixed group.</p><table><tr><th>Band</th><th>Wavelength</th><th>LOW Rrs</th><th>MEDIUM Rrs</th><th>HIGH Rrs</th></tr>'+DATA.bands.map((b,i)=>'<tr><td>'+b+'</td><td>'+DATA.wavelengths[i]+' nm</td>'+groups.map(g=>'<td>'+median(s.roi.filter(r=>r.group===g).map(r=>r.final[i]/Math.PI)).toFixed(6)+' sr⁻¹</td>').join('')+'</tr>').join('')+'</table><p class=\"small\"><b>Definition:</b> approximate Rrs = final retained BOA reflectance / π. These are satellite-derived values, not field validation.</p>'}")
    html = html.replace('<h2>Final products</h2>', '<h2>10. Final products</h2>')
    html = html.replace('<h2>Archive selection</h2>', '<h2>Appendix. All-scene archive summary</h2>')
    html = html.replace(
        ";h+=evidencePanelSet(s.figures.before_cycle0_panels,'1.",
        ";h+=gateExplanation(s);h+=evidencePanelSet(s.figures.before_cycle0_panels,'1.",
        1,
    )
    html = html.replace(
        "4. What do all HydroLight possibilities and fitted kG contribute?",
        "4. What do the selected HydroLight water and fitted kG contribute?",
    )
    html = html.replace(
        "The plotted water curve is the retained best-supported match for each ROI.",
        "The main graphs show only three group-median curves; individual ROI lines are omitted for readability. The orange curve is the median selected HydroLight match, not all 588 simulations.",
    )
    html = html.replace(
        "['LOW ROIs: Cycle 0, Cycle 1 candidate and matched water','MEDIUM ROIs: Cycle 0, Cycle 1 candidate and matched water','HIGH ROIs: Cycle 0, Cycle 1 candidate and matched water']",
        "['LOW median: Cycle 0, Cycle 1 candidate and selected water','MEDIUM median: Cycle 0, Cycle 1 candidate and selected water','HIGH median: Cycle 0, Cycle 1 candidate and selected water']",
    )
    html = html.replace(
        "The removable candidate is kG, not the HydroLight water. HydroLight is a physical possibility library, not the true Tidung answer.",
        "Teal is Cycle 0. Blue is the Cycle-1 candidate after subtracting kG. Orange is the selected possible HydroLight water. The question is whether blue moves from teal toward orange safely; orange is supporting model context, not true Tidung water.",
    )
    html = re.sub(
        r"h\+=evidencePanelSet\(s\.figures\.before_cycle0_panels,'1\..*?\);h\+=evidencePanelSet\(s\.figures\.known_panels",
        "h+=beforeComparison(s);h+=evidenceFigure(s.figures.known",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"h\+=evidenceFigure\(s\.figures\.known,'2\..*?\);h\+=evidenceFigure\(s\.figures\.residual",
        "h+=evidenceFigure(s.figures.known,'2. Can the calculation recover glint when the answer is known?','Known glint is deliberately added, hidden from the calculation, and then estimated. Open the full-size original figure to read all three panels.','Success means the estimated glint approaches the known added glint and the corrected spectrum returns toward the known clean water. This controlled test establishes detection capability; it is not a real-scene truth test.');h+=evidenceFigure(s.figures.residual",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"h\+=evidencePanelSet\(s\.figures\.fit_panels,'4\..*?\);h\+=evidenceFigure\(s\.figures\.spatial",
        "h+=fitComparison(s,e);h+=evidenceFigure(s.figures.spatial",
        html,
        count=1,
        flags=re.S,
    )
    detailed_out = ROOT / "Tidung_All_Scene_Results.html"
    detailed_out.write_text(html, encoding="utf-8")

    # Make the user's original concept document the primary report.  Results are
    # a third top-level tab in that same interface (not an outer wrapper around it).
    if not concept_source.exists():
        raise FileNotFoundError(concept_source)
    merged = concept_source.read_text(encoding="utf-8")
    equation_css = '''
.signal-equation{display:grid;grid-template-columns:1.25fr auto 1fr auto 1fr auto 1fr;align-items:stretch;gap:10px;margin:22px 0}.signal-equation .term{border:2px solid #111827;border-radius:9px;padding:16px;text-align:center;background:#fff}.signal-equation .term b{display:block;font-size:1.17rem}.signal-equation .term span{display:block;color:#475569;font-size:.92rem;line-height:1.35;margin-top:5px}.signal-equation .op{align-self:center;font-size:2rem;font-weight:700}.signal-equation .measured{background:#eff6ff;border-color:#2563eb}.signal-equation .remove{background:#fff7ed;border-color:#ea580c}.signal-equation .keep{background:#f0fdf4;border-color:#16a34a}@media(max-width:900px){.signal-equation{grid-template-columns:1fr}.signal-equation .op{text-align:center}}
'''
    merged = merged.replace('</style>', equation_css + '</style>', 1)
    old_equation = '''<div class="equation">Y(λ,x) = W<sub>j</sub>(λ) + k(x)G(λ,x) + ε(λ,x)<br>after ACOLITE = possible water + possible residual glint + unexplained error</div>'''
    new_equation = '''<p><b>What must be separated:</b> the spectrum measured after ACOLITE contains three kinds of signal. Only the orange part is considered for further removal.</p><div class="signal-equation"><div class="term measured"><b>Measured after ACOLITE</b><span>Y: satellite spectrum at one water location</span></div><div class="op">=</div><div class="term keep"><b>Real water</b><span>W: brightness that HydroLight shows water may produce — keep</span></div><div class="op">+</div><div class="term remove"><b>Remaining glint</b><span>k × G: glint shape G multiplied by unknown amount k — estimate and test</span></div><div class="op">+</div><div class="term"><b>Other error</b><span>ε: atmosphere, adjacency, bottom or noise — do not remove as glint</span></div></div><div class="equation">Measured spectrum = possible water + estimated remaining glint + other unexplained error</div>'''
    merged = merged.replace(old_equation, new_equation, 1)
    merged = merged.replace(
        '<button class="tab-button" data-tab="example">2 · Successful Tidung example</button>',
        '<button class="tab-button" data-tab="calculation">2 · Calculation example</button>',
        1,
    )
    merged = merged.replace(
        '</nav>',
        '<button class="tab-button" data-tab="all-results">3 · Results</button><button class="tab-button" data-tab="code">4 · Code</button></nav>',
        1,
    )
    # The former one-scene success story is now represented in the unified
    # Results page through the scene selector; remove the obsolete hidden panel.
    merged = re.sub(r'<section id="example" class="panel">.*?</section>', '', merged, count=1, flags=re.S)
    calculation_panel = '''
<section id="calculation" class="panel">
  <h2>Numerical example: how glint is added, estimated and removed</h2>
  <div class="note"><b>Purpose:</b> this is a small teaching example with illustrative values. It explains the calculation; it is not claimed to be the measured Tidung answer.</div>
  <div class="box"><h3>The four symbols used in this example</h3><table><tr><th>Symbol</th><th>Simple meaning</th><th>Example</th></tr><tr><td><b>W</b></td><td>Clean water spectrum with no glint. In the controlled example we choose it from HydroLight, so its value is known.</td><td>[0.0120, 0.0080, 0.0020]</td></tr><tr><td><b>G</b></td><td>The relative glint shape: how one unit of glint is distributed between Blue, Green and Red. G describes shape only, not strength.</td><td>[0.70, 0.85, 1.00]</td></tr><tr><td><b>k</b></td><td>One number controlling how strong the glint is. A larger k lifts the spectrum farther above clean water.</td><td>0.0020</td></tr><tr><td><b>kG</b></td><td>The actual glint spectrum added or removed in every band: multiply k by every number in G.</td><td>[0.00140, 0.00170, 0.00200]</td></tr><tr><td><b>C</b></td><td>The contaminated observation created for this controlled test: clean water plus the known added glint.</td><td>C = W + kG</td></tr></table></div>
  <svg viewBox="0 0 1100 300" style="width:100%;border:1px solid #94a3b8;background:white" role="img" aria-label="Flow showing clean water plus glint equals contaminated observation"><rect width="1100" height="300" fill="white"/><text x="550" y="34" text-anchor="middle" font-size="25" font-weight="700">What is created in the controlled example?</text><rect x="35" y="78" width="245" height="145" rx="12" fill="#ecfdf5" stroke="#14836f" stroke-width="3"/><text x="157" y="118" text-anchor="middle" font-size="28" font-weight="700">W</text><text x="157" y="150" text-anchor="middle" font-size="20">clean water</text><text x="157" y="183" text-anchor="middle" font-size="17">keep this signal</text><text x="315" y="161" text-anchor="middle" font-size="40" font-weight="700">+</text><rect x="350" y="78" width="290" height="145" rx="12" fill="#fff7ed" stroke="#ea580c" stroke-width="3"/><text x="495" y="118" text-anchor="middle" font-size="28" font-weight="700">k × G = kG</text><text x="495" y="150" text-anchor="middle" font-size="20">known added glint</text><text x="495" y="183" text-anchor="middle" font-size="17">amount × spectral shape</text><text x="678" y="161" text-anchor="middle" font-size="40" font-weight="700">=</text><rect x="720" y="78" width="340" height="145" rx="12" fill="#fef2f2" stroke="#dc2626" stroke-width="3"/><text x="890" y="118" text-anchor="middle" font-size="28" font-weight="700">C = W + kG</text><text x="890" y="150" text-anchor="middle" font-size="20">contaminated observation</text><text x="890" y="183" text-anchor="middle" font-size="17">the red curve in the graph</text><path d="M 890 228 L 890 270 L 500 270" fill="none" stroke="#2563eb" stroke-width="3" marker-end="url(#arr)"/><defs><marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#2563eb"/></marker></defs><text x="690" y="260" text-anchor="middle" font-size="17" fill="#1d4ed8">Later: estimate kG and subtract it from C to recover W</text></svg>
  <h3>2.1 Start with possible clean water</h3>
  <p>HydroLight supplies a possible glint-free water spectrum <b>W</b>. For three example bands:</p>
  <div class="equation">W = [Blue 0.0120, Green 0.0080, Red 0.0020]</div>
  <div class="box"><b>How the HydroLight library used here was defined</b><ul><li>36 directly simulated training cases: chlorophyll-a = 0.05, 0.20, 0.50 mg m⁻³; CDOM absorption at 440 nm = 0.01, 0.04, 0.10 m⁻¹; NAP/TSM = 0.25, 0.75, 1.50, 3.00 g m⁻³.</li><li>The training grid was interpolated to 7 chlorophyll values × 7 CDOM values × 12 NAP/TSM values = <b>588 possible water spectra</b>.</li><li>The controlled library used SZA 20.42° and wind 5 m s⁻¹. These are tested model conditions, not measurements proving the true water properties of every Tidung scene.</li><li>For a real ROI, the method does not choose one water spectrum beforehand. It fits a separate non-negative k for every one of the 588 water spectra, compares all 588 water-plus-glint fits, and uses HydroLight only to prevent plausible water brightness from being automatically removed as glint.</li></ul></div>
  <div class="pass"><b>Important: HydroLight does not generate the glint.</b><p>At one ROI, the satellite/ACOLITE products provide one local glint-shape vector G. The same G is used while all 588 possible water spectra are tested. What changes between tests is the possible water W<sub>j</sub> and the fitted amount k<sub>j</sub>.</p><div class="equation">For j = 1…588: fit k<sub>j</sub> ≥ 0 → calculate W<sub>j</sub> + k<sub>j</sub>G → calculate RMSE<br>Select (j*, k*) with the smallest valid error<br>Candidate residual glint = k*G</div><p>The orange HydroLight line later shown for an ROI is <b>W<sub>j*</sub></b>, the water member of the selected pair. It is not an average of all simulations and is not declared to be the true Tidung water.</p></div>
  <h3>2.2 Define the glint shape</h3>
  <p><b>G</b> tells us how one unit of surface reflection is distributed among bands. It is a relative shape, not yet the glint amount.</p>
  <div class="equation">G = [Blue 0.70, Green 0.85, Red 1.00]</div>
  <h3>2.3 Choose the known glint amount for the controlled test</h3>
  <p>For validation only, choose a known strength <b>k<sub>true</sub> = 0.0020</b>. Multiply every value in G by k:</p>
  <div class="equation">kG = 0.0020 × [0.70, 0.85, 1.00]<br>= [0.00140, 0.00170, 0.00200]</div>
  <p>This orange vector is the exact band-by-band glint deliberately added in the controlled experiment.</p>
  <h3>2.4 Create the contaminated spectrum</h3>
  <div class="equation">C = W + kG<br>[0.01340, 0.00970, 0.00400] = [0.0120, 0.0080, 0.0020] + [0.00140, 0.00170, 0.00200]</div>
  <svg viewBox="0 0 1000 500" style="width:100%;border:1px solid #94a3b8;background:white" role="img" aria-label="Illustration of water plus glint and recovery"><rect width="1000" height="500" fill="white"/><text x="500" y="38" text-anchor="middle" font-size="25" font-weight="700">Illustrative spectral calculation</text><line x1="90" y1="385" x2="950" y2="385" stroke="#111" stroke-width="2"/><line x1="90" y1="75" x2="90" y2="385" stroke="#111" stroke-width="2"/><text x="170" y="425" text-anchor="middle" font-size="19">Blue</text><text x="520" y="425" text-anchor="middle" font-size="19">Green</text><text x="870" y="425" text-anchor="middle" font-size="19">Red</text><text x="25" y="235" text-anchor="middle" font-size="18" transform="rotate(-90 25 235)">Reflectance</text><polyline points="170,145 520,225 870,345" fill="none" stroke="#14836f" stroke-width="10"/><polyline points="170,110 520,183 870,295" fill="none" stroke="#dc2626" stroke-width="9"/><polyline points="170,145 520,225 870,345" fill="none" stroke="#2563eb" stroke-width="5" stroke-dasharray="15 9"/><line x1="115" y1="62" x2="160" y2="62" stroke="#14836f" stroke-width="8"/><text x="170" y="69" font-size="17">Original clean water W</text><line x1="375" y1="62" x2="420" y2="62" stroke="#dc2626" stroke-width="8"/><text x="430" y="69" font-size="17">Contaminated W + kG</text><line x1="680" y1="62" x2="725" y2="62" stroke="#2563eb" stroke-width="5" stroke-dasharray="12 7"/><text x="735" y="69" font-size="17">Recovered C − estimated kG</text><rect x="115" y="442" width="770" height="42" rx="7" fill="#eff6ff" stroke="#2563eb"/><text x="500" y="469" text-anchor="middle" font-size="18" font-weight="700">The blue dashed recovery lies on top of the green line: overlap is the intended successful result.</text></svg>
  <h3>2.5 Hide k and ask the method to estimate it</h3>
  <p>The calculation receives C, possible HydroLight spectra and G—but not k<sub>true</sub>. It tests non-negative k values and selects the combination W<sub>j</sub> + kG closest to C.</p>
  <div class="equation">(selected water, estimated k) = combination with the smallest spectral RMSE</div>
  <p>Example result: <b>k<sub>estimated</sub> = 0.0019</b>. “Known versus estimated glint” therefore compares <b>0.0020G</b> with <b>0.0019G</b>. Similar curves mean the controlled calculation recovered the glint we deliberately added.</p>
  <h3>2.6 Remove the estimate and check recovery</h3>
  <div class="equation">Recovered water = C − k<sub>estimated</sub>G</div>
  <p>If the recovered blue curve returns close to the original green W curve, the known-answer test passes. For real Tidung data there is no known W, so this controlled success is only method validation; B11/B12, spatial ordering, safety QC and the repeated residual test are still required.</p>
  <div class="note"><b>Do not confuse the controlled example with a real scene:</b> C exists here because we deliberately create W + kG and therefore know the answer. In the real-scene calculation, the input Y is the measured spectrum after Cycle 0. We test 588 possible W values and estimate k; there is no known clean-water truth C or W for the real satellite pixel.</div>
</section>
'''
    result_panel = '''
<section id="all-results" class="panel">
  <div class="section-head">
    <div><span class="eyebrow">ALL RETAINED SCENES</span><h2>Processed-scene results and products</h2></div>
    <p>Select a scene, compare original/first-correction/final images, inspect all 30 ROI spectra, and download BOA, Rrs and rrs products.</p>
  </div>
  <iframe title="All Tidung processed-scene results" src="Tidung_All_Scene_Results.html?v=20260913e" style="width:100%;height:calc(100vh - 180px);min-height:850px;border:2px solid #111;background:#fff"></iframe>
</section>
'''
    portable = ROOT / "Tidung_Glint_Pipeline"
    code_sources = [
        ("README: installation, configuration and execution", portable / "README.md"),
        ("Portable command-line runner", portable / "run_pipeline.py"),
        ("Desktop GUI example", portable / "gui.py"),
        ("Input and configuration validator", portable / "validate_setup.py"),
        ("Complete residual-glint experiment", portable / "scripts" / "run_tidung_full_residual_glint_experiment.py"),
        ("All-scene batch runner", portable / "scripts" / "run_tidung_all_scenes_residual_glint_experiment.py"),
        ("Controlled HydroLight known-glint validation", portable / "scripts" / "run_tidung_controlled_hydrolight_glint_validation.py"),
        ("Final BOA, Rrs and rrs product exporter", portable / "scripts" / "export_tidung_production_products.py"),
        ("Per-pixel Rrs and rrs CSV exporter", PROJECT / "scripts" / "export_tidung_pixel_rrs_csv.py"),
        ("Per-pixel Rrs and rrs Excel exporter", PROJECT / "scripts" / "build_tidung_pixel_rrs_xlsx.py"),
        ("Interactive HTML report builder", portable / "scripts" / "build_tidung_final_products_html.py"),
        ("Conda environment", portable / "environment.yml"),
        ("Pip requirements", portable / "requirements.txt"),
        ("Example path configuration", portable / "config.example.json"),
    ]
    code_dir = ROOT / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    code_parts = []
    for title, source_path in code_sources:
        if not source_path.exists():
            continue
        target = code_dir / source_path.name
        shutil.copy2(source_path, target)
        escaped = html_lib.escape(source_path.read_text(encoding="utf-8", errors="replace"))
        code_parts.append(f'''<details class="figure"><summary style="font-size:1.2rem;font-weight:700;cursor:pointer">{title}</summary><p><a href="code/{target.name}" download>Download {target.name}</a></p><pre style="white-space:pre;overflow:auto;max-height:75vh;background:#0f172a;color:#e2e8f0;padding:18px;font-size:14px;line-height:1.45">{escaped}</pre></details>''')
    code_panel = f'''<section id="code" class="panel"><h2>Python processing project</h2><div class="pass">Create the Conda/venv environment, copy <code>config.example.json</code> to <code>config.json</code>, set the data paths, validate the setup, and run the processing pipeline. <a href="Tidung_Glint_Pipeline/README.md" target="_blank">Open the complete README</a>.</div><p>The project is stored in <code>Tidung_Glint_Pipeline/</code>. Its principal files are readable and downloadable below.</p>{''.join(code_parts)}</section>'''
    merged = merged.replace(
        '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
        calculation_panel + result_panel + code_panel + '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
        1,
    )
    # OSM is blocked in the target environment; keep only Esri satellite/default.
    old_tile = "L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(m);"
    new_tile = "const imagery=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Tiles © Esri'});const street=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Tiles © Esri'});street.addTo(m);L.control.layers({'Esri default map':street,'Esri satellite':imagery}).addTo(m);"
    merged = merged.replace(old_tile, new_tile)
    # Leaflet maps are created while their tab is hidden. Re-fit after the tab
    # becomes visible so the image opens directly over Tidung.
    merged = merged.replace(
        "setTimeout(()=>maps.forEach(m=>m.invalidateSize()),80)",
        "setTimeout(()=>{maps.forEach(m=>{m.invalidateSize();if(b.dataset.tab==='example')m.fitBounds([[-5.82526960465885,106.46469848255522],[-5.774789209564791,106.54013804997781]],{padding:[8,8]})});const f=document.querySelector('#all-results iframe');if(f&&b.dataset.tab==='all-results')f.contentWindow.postMessage('fit-tidung','*')},180)",
    )
    shutil.copytree(concept_assets, ROOT / "glint-concept-v6-assets", dirs_exist_ok=True)
    out = ROOT / "Tidung_Glint_Correction_Results.html"
    out.write_text(merged, encoding="utf-8")
    print(json.dumps({"html": str(out), "scenes": len(scene_data), "assets": len(list(ASSETS.rglob('*.png')))}, indent=2))


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tidung Glint-Correction Results</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%230b4f6c'/%3E%3Cpath d='M8 37c12-12 20 12 32 0s16 0 16 0v13H8z' fill='%235fd1c8'/%3E%3Ccircle cx='44' cy='18' r='7' fill='%23ffd166'/%3E%3C/svg%3E">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--ink:#111827;--muted:#526071;--line:#cbd5e1;--blue:#0b4f6c;--teal:#087f78;--paper:#fff;--soft:#f3f6f8;--orange:#b45309}*{box-sizing:border-box}body{margin:0;background:var(--soft);color:var(--ink);font:17px/1.55 Arial,sans-serif}header{background:#fff;border-bottom:1px solid var(--line);padding:18px 24px;position:sticky;top:0;z-index:1000}.top{max-width:1500px;margin:auto;display:flex;gap:20px;align-items:center;justify-content:space-between}h1{font-size:1.55rem;margin:0}select,button,.button{font:inherit;padding:9px 12px;border:1px solid #94a3b8;border-radius:6px;background:white;color:var(--ink)}nav{max-width:1500px;margin:12px auto 0;display:flex;gap:8px}.tab{font-weight:700}.tab.active{background:var(--blue);color:white}.page{max-width:1500px;margin:18px auto;padding:0 18px}.panel{display:none}.panel.active{display:block}.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:18px;margin-bottom:16px}h2{font-size:1.45rem;margin:0 0 12px}h3{font-size:1.12rem;margin:0 0 8px}.status{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:10px}.metric{border:1px solid var(--line);padding:12px;background:#fff}.metric b{display:block;font-size:1.35rem}.maps{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.map{height:430px;border:1px solid #94a3b8}.map-title{font-weight:700;margin-bottom:6px}.note{border-left:5px solid var(--teal);padding:10px 14px;background:#ecfeff}.warn{border-left-color:var(--orange);background:#fff7ed}.chart{width:100%;height:auto;min-height:420px;border:1px solid var(--line);background:#fff}.chart-note{margin:4px 0 12px;color:var(--muted)}.controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:12px}.legend{display:flex;gap:18px;flex-wrap:wrap}.key{display:inline-flex;align-items:center;gap:6px}.swatch{width:24px;height:4px;display:inline-block}.downloads{display:flex;gap:10px;flex-wrap:wrap}.button{text-decoration:none;font-weight:700}.small{font-size:.9rem;color:var(--muted)}table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}.help{display:inline-grid;place-items:center;width:28px;height:28px;padding:0;border-radius:50%;font-weight:800;color:#0b4f6c;border:2px solid #0b4f6c;margin-left:6px;cursor:pointer}.explain-dialog{width:min(760px,92vw);border:2px solid #111827;border-radius:10px;padding:0}.explain-dialog::backdrop{background:#0f172a99}.explain-dialog .inside{padding:22px}.explain-dialog h2{padding-right:80px}.close-help{float:right;font-weight:700}.formula{font:700 1.12rem/1.55 Georgia,serif;background:#eff6ff;border:2px solid #2563eb;padding:14px;text-align:center;margin:14px 0}@media(max-width:950px){.maps,.status{grid-template-columns:1fr}.map{height:350px}.top{align-items:flex-start;flex-direction:column}header{position:static}}
</style></head><body>
<header><div class="top"><div><h1>Tidung Sentinel-2 glint correction</h1><div class="small">Scene evidence and final retained products</div></div><label><b>Scene</b> <select id="sceneSelect"></select></label></div><nav><button class="tab active" data-tab="concept">Correction idea</button><button class="tab" data-tab="results">Scene result</button><button class="tab" data-tab="evidence">Residual-glint analysis</button><button class="tab" data-tab="spectra">30 ROI spectra</button><button class="tab" data-tab="products">Products & QC</button><button class="tab" data-tab="archive">Archive decisions</button></nav></header>
<main class="page">
<section id="concept" class="panel active"><div class="card"><h2>Why and how the correction works</h2><p>The complete correction idea is shown below before the results. It explains the first ACOLITE-style removal, how HydroLight protects possible real-water spectra, how B11/B12 provides independent surface-reflection evidence, and when an additional component may be subtracted.</p></div><iframe title="Tidung residual-glint correction idea" src="concept/glint-correction-idea.html" style="width:100%;height:calc(100vh - 185px);min-height:760px;border:1px solid var(--line);background:white"></iframe></section>
<section id="results" class="panel"><div class="status" id="status"></div><div class="card"><h2>Original, first correction and final retained image</h2><p class="chart-note">All three panels use the same water-focused RGB stretch. The maps open close to Tidung; zoom with the mouse or map controls. Click the water image to open it large.</p><div class="maps"><div><div class="map-title">Original Sentinel-2 L2A</div><div id="map0" class="map"></div><button class="open-large" data-image="before">Open image large</button></div><div><div class="map-title">After first ACOLITE-style correction</div><div id="map1" class="map"></div><button class="open-large" data-image="cycle0">Open image large</button></div><div><div class="map-title">Final retained product</div><div id="map2" class="map"></div><button class="open-large" data-image="final">Open image large</button></div></div></div><div id="decisionText" class="card note"></div></section>
<section id="evidence" class="panel"><div id="evidenceContent"></div></section>
<section id="spectra" class="panel"><div class="card"><h2>All 30 offshore ROI spectra</h2><p class="chart-note">Each thin line is one 7×7-pixel offshore ROI. Use the control to compare original L2A, first correction, and final retained reflectance. Thick lines are LOW, MEDIUM and HIGH group medians.</p><div class="controls"><label><b>Product</b> <select id="stage"><option value="before">Original L2A</option><option value="cycle0">First correction</option><option value="final" selected>Final retained</option></select></label><div class="legend"><span class="key"><i class="swatch" style="background:#2563eb"></i>LOW</span><span class="key"><i class="swatch" style="background:#f59e0b"></i>MEDIUM</span><span class="key"><i class="swatch" style="background:#dc2626"></i>HIGH</span></div></div><svg id="chart" class="chart" role="img" aria-label="Thirty ROI spectra"></svg></div><div class="card note"><b>How to read it:</b> after correction, HIGH-glint ROIs should no longer remain systematically brighter solely because they had stronger original surface reflection. Natural water differences may remain; equal spectra are not required.</div></section>
<section id="products" class="panel"><div class="card"><h2>Final products</h2><div class="downloads" id="downloads"></div></div><div class="card"><h2>Rrs and rrs checks</h2><table id="qcTable"></table><p class="small"><b>Important:</b> Rrs_approx = final L2A BOA reflectance / π. Below-surface rrs_approx = Rrs_approx / (0.52 + 1.7 Rrs_approx). These conversions passed numeric checks, but they are not field-validated water-leaving reflectance. Benthic and bathymetry models still require calibration and validation.</p></div></section>
<section id="archive" class="panel"><div class="card"><h2>Archive selection</h2><p>The complete ledger below distinguishes initial rejection, eligible-but-unprocessed data, processed rejection, Cycle-0 retention and Cycle-1 retention. “Not processed” is not a scientific rejection.</p><div id="archiveSummary" class="status"></div><table id="archiveTable"></table><div class="downloads"><a class="button" target="_blank" href="00_MASTER_QC/all_80_L2A_scene_inventory.csv">All 80 scenes</a><a class="button" target="_blank" href="00_MASTER_QC/strict_33_scene_final_decisions.csv">33 processed decisions</a><a class="button" target="_blank" href="00_MASTER_QC/retained_scene_downstream_QC.csv">25 retained-scene QC</a><a class="button" target="_blank" href="00_MASTER_QC/product_manifest.csv">Product manifest</a></div></div></section>
</main>
<dialog id="lightbox" style="max-width:96vw;max-height:96vh;border:1px solid #64748b;padding:12px"><button id="closeLightbox" style="float:right;font-weight:700">Close</button><h2 id="lightboxTitle">Image</h2><img id="lightboxImage" alt="Large corrected water image" style="display:block;max-width:92vw;max-height:82vh;image-rendering:auto"></dialog>
<dialog id="explainDialog" class="explain-dialog"><div class="inside"><button class="close-help" onclick="document.getElementById('explainDialog').close()">Close</button><h2 id="explainTitle">Explanation</h2><div id="explainBody"></div></div></dialog>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const DATA=__DATA__;let current=0;const colors={LOW:'#2563eb',MEDIUM:'#f59e0b',HIGH:'#dc2626'};const maps=[];
function initMaps(){for(let i=0;i<3;i++){const m=L.map('map'+i,{zoomControl:true});const imagery=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{attribution:'Tiles © Esri'});const street=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',{attribution:'Tiles © Esri'});street.addTo(m);L.control.layers({'Esri default map':street,'Esri satellite':imagery}).addTo(m);maps.push(m);new ResizeObserver(()=>{if(m.getContainer().clientWidth>0){m.invalidateSize();const s=DATA.scenes[current];m.fitBounds(s.bounds,{padding:[8,8]})}}).observe(m.getContainer())}maps.forEach(m=>m.on('moveend zoomend',()=>{if(window.syncing)return;window.syncing=true;maps.forEach(o=>{if(o!==m)o.setView(m.getCenter(),m.getZoom(),{animate:false})});window.syncing=false}))}
function fitSelectedScene(){const s=DATA.scenes[current];maps.forEach(m=>{m.invalidateSize();m.fitBounds(s.bounds,{padding:[8,8],animate:false})})}
window.addEventListener('message',e=>{if(e.data==='fit-tidung')setTimeout(fitSelectedScene,80)});
window.addEventListener('resize',()=>setTimeout(fitSelectedScene,80));
// This page is loaded inside a hidden parent tab. Wait until the iframe has a
// real visible rectangle, then perform the first reliable fit to Tidung.
const visibleFitTimer=setInterval(()=>{try{const frame=window.frameElement;const visible=!frame||frame.getBoundingClientRect().width>0;if(visible&&document.documentElement.clientWidth>0){fitSelectedScene();clearInterval(visibleFitTimer)}}catch(e){fitSelectedScene();clearInterval(visibleFitTimer)}},250);
function metric(label,value){return `<div class="metric"><span>${label}</span><b>${value}</b></div>`}
const HELP={lod:['Detection limit','The method is first run on 2,500 controlled trials made from 10 low-glint ROIs, where no residual glint is added. Any positive fitted component is therefore a false signal caused by noise or imperfect water matching. The limit is the 95th percentile of those false fitted components. A real-ROI value must be larger than this limit; passing it is only one test, not final proof of glint.'],rmse:['RMSE-improvement limit','RMSE measures the average band-by-band mismatch between the observed spectrum and W + kG. In zero-glint trials, fitting can improve RMSE slightly by chance. The 95th percentile of those false improvements becomes the minimum required improvement.'],shape:['Spectral-shape similarity','This compares the fitted extra component with the expected smooth glint direction G. The cutoff is calibrated from controlled cases containing known injected glint. A one-band spike or water-like feature should not pass.'],corr:['B11/B12 relationship','Each of the 30 ROIs has an original B11/B12 surface-reflection indicator and a fitted residual amount k. Spearman r measures whether ROIs with stronger original surface reflection also require more fitted residual. The rule used here is r ≥ 0.30 and p ≤ 0.10.'],pvalue:['p-value','A p-value measures how compatible the observed ordering is with no systematic relationship. The one-sided HIGH-greater-than-LOW test uses p ≤ 0.05. A small p-value supports the ordering, but it does not measure the amount of glint.'],counts:['LOW and HIGH detection counts','The scene rule requires no more than 1 of 10 LOW ROIs and at least 5 of 10 HIGH ROIs to pass the complete ROI detector. This checks that detections concentrate where original glint was strongest instead of appearing everywhere.'],highlow:['HIGH minus LOW','This is the median fitted additional component in the HIGH group minus the median in the LOW group. Positive means the stronger original-glint group retains more extra brightness. The current implementation compares it with the individual-component detection limit; this group-difference rule is methodological and should be recalibrated with a null bootstrap before being called independently validated.'],k:['Fitted k','For each possible HydroLight water Wj, k is the non-negative scale that makes Wj + kG closest to the Cycle-0 spectrum Y. One k is calculated for each of 588 water possibilities. The selected pair has the smallest valid spectral RMSE; the removable candidate is kG, not k alone.']};
HELP.swir=['B11/B12 surface-reflection reference','This is not B11 divided by B12. The program forms one glint candidate from B11 and another from B12 after atmospheric/Fresnel wavelength transfer. At each pixel it selects the smaller valid candidate, then stores the corresponding non-negative B11 or B12 reflectance as ρg,ref. The ROI indicator is the mean of ρg,ref across its 7 × 7 pixels.'];
function helpButton(key,label='?'){return `<button class="help" aria-label="Open explanation" onclick="showHelp('${key}')">${label}</button>`}
function showHelp(key){const h=HELP[key];document.getElementById('explainTitle').textContent=h[0];document.getElementById('explainBody').innerHTML=`<p>${h[1]}</p>`;document.getElementById('explainDialog').showModal()}
function evidenceFigure(src,title,interpretation,conclusion){if(!src)return '';return `<div class="card"><h2>${title}</h2><img src="${src}" alt="${title}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8;cursor:zoom-in" onclick="open(this.src,'_blank')"><p><b>Interpretation:</b> ${interpretation}</p><p class="note"><b>Conclusion:</b> ${conclusion}</p></div>`}
function evidencePanelSet(srcs,title,interpretation,labels,conclusion){if(!srcs||!srcs.length)return '';return `<div class="card"><h2>${title}</h2>${srcs.map((src,i)=>`<figure style="margin:20px 0 34px"><h3>${labels[i]||('Panel '+(i+1))}</h3><a href="${src}" target="_blank"><img src="${src}" alt="${labels[i]||title}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8"></a><figcaption class="chart-note">Open the graph to inspect the full-size values.</figcaption></figure>`).join('')}<p><b>Interpretation:</b> ${interpretation}</p><p class="note"><b>Conclusion:</b> ${conclusion}</p></div>`}
function spectrumSvg(s,stage,title){const groups=['LOW','MEDIUM','HIGH'],W=1000,H=500,p={l:90,r:35,t:95,b:70};const gm={};groups.forEach(g=>gm[g]=DATA.bands.map((_,i)=>median(s.roi.filter(r=>r.group===g).map(r=>r[stage][i]))));const vals=groups.flatMap(g=>gm[g]),lo=Math.min(0,Math.min(...vals)*.95),hi=Math.max(...vals)*1.08,X=x=>p.l+(x-DATA.wavelengths[0])/(DATA.wavelengths.at(-1)-DATA.wavelengths[0])*(W-p.l-p.r),Y=y=>H-p.b-(y-lo)/(hi-lo)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/><text x="${W/2}" y="30" text-anchor="middle" font-size="24" font-weight="700">${title}</text>`;groups.forEach((g,i)=>{const x=315+i*155;z+=`<line x1="${x}" x2="${x+38}" y1="66" y2="66" stroke="${colors[g]}" stroke-width="6"/><text x="${x+48}" y="72" font-size="16">${g}</text>`});for(let j=0;j<5;j++){const v=lo+(hi-lo)*j/4;z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#dbe3ea"/><text x="${p.l-10}" y="${Y(v)+5}" text-anchor="end" font-size="14">${v.toFixed(3)}</text>`}groups.forEach(g=>{const pts=gm[g].map((v,i)=>`${X(DATA.wavelengths[i])},${Y(v)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${colors[g]}" stroke-width="5"/>`;gm[g].forEach((v,i)=>z+=`<circle cx="${X(DATA.wavelengths[i])}" cy="${Y(v)}" r="5" fill="${colors[g]}"/>`)});DATA.wavelengths.forEach(w=>z+=`<text x="${X(w)}" y="${H-34}" text-anchor="middle" font-size="14">${w}</text>`);z+=`<text x="${W/2}" y="${H-7}" text-anchor="middle" font-size="17">Wavelength (nm)</text><text transform="translate(24 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle" font-size="17">BOA reflectance</text>`;return `<svg viewBox="0 0 ${W} ${H}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8">${z}</svg>`}
function highLowSummary(s){const med=(stage,g)=>DATA.bands.map((_,i)=>median(s.roi.filter(r=>r.group===g).map(r=>r[stage][i]))),hb=med('before','HIGH'),lb=med('before','LOW'),ha=med('cycle0','HIGH'),la=med('cycle0','LOW'),db=hb.map((v,i)=>v-lb[i]),da=ha.map((v,i)=>v-la[i]),meanAbs=x=>x.reduce((q,v)=>q+Math.abs(v),0)/x.length,mb=meanAbs(db),ma=meanAbs(da),change=mb?100*(mb-ma)/mb:0;const W=1000,H=500,p={l:100,r:35,t:100,b:70},lo=Math.min(0,...db,...da)*1.15,hi=Math.max(0,...db,...da)*1.15||.001,X=i=>p.l+i/(DATA.bands.length-1)*(W-p.l-p.r),Y=v=>H-p.b-(v-lo)/(hi-lo)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/><text x="${W/2}" y="30" text-anchor="middle" font-size="24" font-weight="700">HIGH minus LOW before and after Cycle 0</text><line x1="280" x2="325" y1="68" y2="68" stroke="#334155" stroke-width="6"/><text x="335" y="74" font-size="16">Original L2A</text><line x1="535" x2="580" y1="68" y2="68" stroke="#0f766e" stroke-width="6"/><text x="590" y="74" font-size="16">After Cycle 0</text>`;for(let j=0;j<5;j++){const v=lo+(hi-lo)*j/4;z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#dbe3ea"/><text x="${p.l-10}" y="${Y(v)+5}" text-anchor="end" font-size="14">${v.toFixed(4)}</text>`}z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(0)}" y2="${Y(0)}" stroke="#111827" stroke-width="2"/>`;const line=(v,c)=>{z+=`<polyline points="${v.map((q,i)=>`${X(i)},${Y(q)}`).join(' ')}" fill="none" stroke="${c}" stroke-width="5"/>`;v.forEach((q,i)=>z+=`<circle cx="${X(i)}" cy="${Y(q)}" r="5" fill="${c}"/>`)};line(db,'#334155');line(da,'#0f766e');DATA.bands.forEach((band,i)=>z+=`<text x="${X(i)}" y="${H-36}" text-anchor="middle" font-size="15">${band}</text>`);z+=`<text x="${W/2}" y="${H-8}" text-anchor="middle" font-size="17">Sentinel-2 band</text><text transform="translate(25 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle" font-size="16">HIGH median − LOW median</text>`;const rows=DATA.bands.map((band,i)=>`<tr><td>${band}</td><td>${db[i].toFixed(6)}</td><td>${da[i].toFixed(6)}</td><td>${Math.abs(da[i])<Math.abs(db[i])?'Closer to zero':'Not closer to zero'}</td></tr>`).join('');return `<div class="card"><h2>6. HIGH–LOW separation</h2><div class="formula">HIGH–LOW separation = HIGH group median − LOW group median</div><svg viewBox="0 0 ${W} ${H}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8">${z}</svg><p><b>Interpretation:</b> values closer to zero after Cycle 0 indicate that the original HIGH–LOW ordering became smaller. A sign change means that the ordering reversed.</p><p class="note"><b>Conclusion:</b> ${change>0?'the mean absolute HIGH–LOW separation decreased by '+change.toFixed(1)+'%.':'the mean absolute HIGH–LOW separation did not decrease.'} This supports only the group comparison; residual glint is tested later.</p><details><summary><b>Band values</b></summary><table><tr><th>Band</th><th>Original HIGH−LOW</th><th>Cycle 0 HIGH−LOW</th><th>Result</th></tr>${rows}</table></details></div>`}
function roiRankingSvg(s){const rs=[...s.roi].sort((a,b)=>a.rhog-b.rhog),W=1100,H=470,p={l:80,r:25,t:65,b:90},lo=Math.min(...rs.map(r=>r.rhog))*.96,hi=Math.max(...rs.map(r=>r.rhog))*1.03,X=i=>p.l+i/(rs.length-1)*(W-p.l-p.r),Y=v=>H-p.b-(v-lo)/(hi-lo)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/><text x="${W/2}" y="32" text-anchor="middle" font-size="24" font-weight="700">Selected ROI values of ρg,ref (small to large)</text>`;for(let j=0;j<5;j++){const v=lo+(hi-lo)*j/4;z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#dbe3ea"/><text x="${p.l-10}" y="${Y(v)+5}" text-anchor="end" font-size="14">${v.toFixed(4)}</text>`}rs.forEach((r,i)=>{z+=`<circle cx="${X(i)}" cy="${Y(r.rhog)}" r="7" fill="${colors[r.group]}"/><text x="${X(i)}" y="${H-58}" transform="rotate(-55 ${X(i)} ${H-58})" text-anchor="end" font-size="12">${r.id}</text>`});[9.5,19.5].forEach(i=>z+=`<line x1="${X(i)}" x2="${X(i)}" y1="${p.t}" y2="${H-p.b}" stroke="#111827" stroke-width="2" stroke-dasharray="7 6"/>`);z+=`<text x="${X(4.5)}" y="${H-15}" text-anchor="middle" font-size="17" fill="${colors.LOW}" font-weight="700">LOW: 10 selected</text><text x="${X(14.5)}" y="${H-15}" text-anchor="middle" font-size="17" fill="${colors.MEDIUM}" font-weight="700">MEDIUM: 10 selected</text><text x="${X(24.5)}" y="${H-15}" text-anchor="middle" font-size="17" fill="${colors.HIGH}" font-weight="700">HIGH: 10 selected</text><text transform="translate(20 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle" font-size="17">Selected SWIR reference ρg,ref</text>`;return `<svg viewBox="0 0 ${W} ${H}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8">${z}</svg>`}
function cycle0Calculation(s){const r=s.roi.find(x=>x.group==='HIGH')||s.roi[0],i=0;return `<div class="card"><h2>4. Cycle 0 calculation</h2><div class="formula">Cycle 0 = original L2A − glint estimate used</div><table><tr><th>Real ROI example</th><th>B02 value</th></tr><tr><td>ROI</td><td>${r.id} (${r.group})</td></tr><tr><td>Original L2A</td><td>${r.before[i].toFixed(6)}</td></tr><tr><td>B11-derived glint estimate</td><td>${r.b11CandidateBlue.toFixed(6)}</td></tr><tr><td>B12-derived glint estimate</td><td>${r.b12CandidateBlue.toFixed(6)}</td></tr><tr><td>Glint estimate actually removed in B02</td><td>${r.removed0[i].toFixed(6)}</td></tr><tr><td>Cycle 0 result</td><td>${r.cycle0[i].toFixed(6)}</td></tr><tr><td>Arithmetic check</td><td>${r.before[i].toFixed(6)} − ${r.removed0[i].toFixed(6)} = ${r.cycle0[i].toFixed(6)}</td></tr></table><p><b>Interpretation:</b> the B11- and B12-derived candidates are compared pixel by pixel. The selected source is transferred separately to every visible–NIR band before subtraction.</p><p class="note"><b>Conclusion:</b> Cycle 0 is the first corrected spectrum. It is the input to the later residual-glint test.</p></div>`}
function cycle0Qc(s){return `<div class="card"><h2>8. Cycle 0 quality control</h2><table><tr><th>Check</th><th>Required</th><th>Observed</th><th>Result</th></tr><tr><td>Maximum visible negative pixels</td><td>≤ 1%</td><td>${s.qc.negative.toFixed(3)}%</td><td><b>${s.qc.negative<=1?'PASS':'FAIL'}</b></td></tr><tr><td>Rrs–rrs arithmetic round trip</td><td>Near zero</td><td>${s.qc.roundtrip.toExponential(2)}</td><td><b>${s.qc.roundtrip<1e-6?'PASS':'CHECK'}</b></td></tr></table><p><b>Interpretation:</b> these tests identify obvious over-subtraction and conversion errors. They do not prove field accuracy.</p><p class="note"><b>Conclusion:</b> ${s.qc.negative<=1?'Cycle 0 passed the displayed numerical safety checks.':'Cycle 0 produced excessive negative visible reflectance.'}</p></div>`}
function detectionLimitSection(s){const e=s.evidence;return `<div class="card"><h2>10. Residual-glint detection limit</h2><div class="formula">Detection limit = 95th percentile of fitted components when added glint = 0</div><table><tr><th>Calibration item</th><th>Value</th></tr><tr><td>Zero-added-glint trials</td><td>2,500</td></tr><tr><td>Detection limit</td><td>${e.detectionLimit.toFixed(6)} reflectance</td></tr><tr><td>Observed zero-glint false-positive rate</td><td>${(100*e.zeroFalsePositiveRate).toFixed(1)}%</td></tr><tr><td>Minimum RMSE improvement</td><td>${e.rmseImprovementLimit.toFixed(6)} reflectance</td></tr><tr><td>Minimum shape similarity</td><td>${e.shapeSimilarityLimit.toFixed(3)}</td></tr></table><p><b>Interpretation:</b> a fitted component below ${e.detectionLimit.toFixed(6)} cannot be distinguished reliably from noise or imperfect HydroLight matching. Exceeding it passes only one test.</p><p class="note"><b>Conclusion:</b> an ROI is counted as detected only when magnitude, RMSE improvement and spectral-shape criteria all pass.</p></div>`}
function roiSelectionSection(s){const med=g=>median(s.roi.filter(r=>r.group===g).map(r=>r.rhog));const values=[...s.roi].sort((a,b)=>a.rhog-b.rhog).map((r,i)=>`<tr><td>${i+1}</td><td>${r.id}</td><td>${r.b11CandidateBlue.toFixed(6)}</td><td>${r.b12CandidateBlue.toFixed(6)}</td><td>${r.b11SelectedPercent.toFixed(0)}%</td><td>${r.selectedSwir}</td><td>${r.rhog.toFixed(6)}</td><td>${r.group}</td></tr>`).join('');return `<div class="card"><h2>1. Water mask and offshore ROI selection</h2><p>The analysis uses valid offshore water only. Land, clouds, cloud shadows and invalid pixels are excluded. ROI centres must support a complete 7 × 7 valid-water window, be at least 1 km from mapped land and 500 m inside the image edge, and have local corrected-B04 coefficient of variation ≤ 0.15. These are candidate deep-water ROIs; depth is not independently confirmed.</p><table><tr><th>Item</th><th>Definition used</th><th>Reason</th></tr><tr><td>Number of ROIs</td><td>30: 10 from each scene-wide surface-reference third</td><td>Provides repeated, spatially separated samples across weak-to-strong original surface reflection.</td></tr><tr><td>ROI size</td><td>7 × 7 pixels at 20 m resolution</td><td>Approximately 140 × 140 m; all 49 pixels must be valid water.</td></tr><tr><td>ROI statistics</td><td>Mean spectrum and mean selected SWIR reference across 49 pixels</td><td>Matches the calculation in the processing code.</td></tr><tr><td>Grouping source</td><td>Selected B11-or-B12 SWIR reference ρg,ref ${helpButton('swir')}</td><td>Groups are fixed before correction and reused afterward.</td></tr></table></div>${evidenceFigure(s.figures.roi_map,'Locations of the 30 offshore ROIs','Confirms that the numbered samples lie in the intended offshore water area.','Inspect whether ROIs remain offshore and avoid mapped land. Colours show the fixed scene-wide groups defined in Section 2.') }<div class="card"><h2>2. Construction of the LOW, MEDIUM and HIGH groups</h2><p><b>B11/B12 does not mean B11 ÷ B12.</b> The program calculates a B11-derived blue-band glint candidate and a B12-derived blue-band glint candidate using atmospheric-transmittance and Fresnel transfer factors. At each pixel, the smaller valid candidate determines whether B11 or B12 supplies ρg,ref. ${helpButton('swir')}</p><div class="formula">B11 candidate = K<sub>B02←B11</sub> × max(B11,0)<br>B12 candidate = K<sub>B02←B12</sub> × max(B12,0)<br>Select the smaller valid candidate; its source band supplies ρg,ref</div><p>Across all eligible offshore ROI centres in the scene, the 33⅓% and 66⅔% quantiles of the 7 × 7 mean ρg,ref define LOW, MEDIUM and HIGH candidate pools. Ten spatially separated ROI centres are then selected from each pool. The chart below sorts only the 30 selected ROIs for display; it did not create the boundaries.</p>${roiRankingSvg(s)}<div class="status">${metric('LOW ρg,ref median',med('LOW').toFixed(6))}${metric('MEDIUM ρg,ref median',med('MEDIUM').toFixed(6))}${metric('HIGH ρg,ref median',med('HIGH').toFixed(6))}</div><p class="note"><b>Meaning:</b> a larger ρg,ref means stronger original SWIR surface-reflection reference. It is evidence of relative surface reflection, not a direct measurement proving that all visible brightness is glint.</p><details><summary><b>Show both candidates and the selection for every ROI</b></summary><table><tr><th>Display rank</th><th>ROI</th><th>B11-derived blue candidate</th><th>B12-derived blue candidate</th><th>Pixels selecting B11</th><th>Dominant source</th><th>Mean selected ρg,ref</th><th>Group</th></tr>${values}</table><p class="small">Candidate values are transferred blue-band glint estimates. ρg,ref is the selected raw SWIR reference, so these columns are related but are not numerically identical.</p></details></div>`}
function beforeComparison(s){const labels=['LOW group','MEDIUM group','HIGH group'];const median=evidencePanelSet(s.figures.before_cycle0_median_panels,'Before and after the first correction','Each graph shows the median of 10 ROIs, so labels and spectral changes remain readable.',labels,'Dark gray = original Sentinel-2 L2A. Teal = Cycle 0 after the first ACOLITE-style correction. A lower teal curve shows the amount removed by the first correction; it does not by itself prove that no residual glint remains.');const all=evidenceFigure(s.figures.before_cycle0,'All 10 ROI spectra before and after Cycle 0','Open the full-size figure to inspect every ROI without cutting the original three-panel graph.','Thin lines are individual ROIs and thick lines are group medians.');return `<div class="card"><h2>Cycle 0 spectral change</h2><label><b>Graph view</b> <select onchange="document.getElementById('beforeMedian').style.display=this.value==='median'?'block':'none';document.getElementById('beforeAll').style.display=this.value==='all'?'block':'none'"><option value="median" selected>Median only</option><option value="all">All 10 ROIs</option></select></label></div><div id="beforeMedian">${median}</div><div id="beforeAll" style="display:none">${all}</div>`}
function fitComparison(s,e){const labels=['LOW group','MEDIUM group','HIGH group'];const medianRead=s.extra?'Green is Cycle 0, blue is the final retained Cycle 1, and orange is the closest physically possible HydroLight water. The blue curve should move safely toward the orange curve without becoming negative.':'Green is the final retained Cycle 0. Orange is the closest possible HydroLight water used only to test whether unexplained brightness could be water. No Cycle-1 result is shown because additional subtraction was rejected.';const medianTitle=s.extra?'Cycle 0, retained Cycle 1 and closest possible water':'Final Cycle 0 and closest possible water';const median=evidencePanelSet(s.figures.fit_median_panels,medianTitle,'This graph answers whether the retained spectrum is physically compatible with one member of the HydroLight water library.',labels,medianRead);if(!s.extra)return `<div class="card"><h2>6. Closest possible water and the decision not to subtract more</h2><p><b>Conclusion:</b> Cycle 1 was not authorized. The graph below therefore contains the retained Cycle 0 and HydroLight context only. No hypothetical corrected curve is presented as a result.</p></div>${median}<details class="card"><summary><b>Optional rejected-fit diagnostic</b></summary><p>The fitting program necessarily calculated a hypothetical subtraction to test it. It failed the complete acceptance rule and was never written into the final product. Open the source diagnostic only when auditing that rejection.</p><p><a href="${s.figures.fit}" target="_blank">Open hypothetical diagnostic — NOT APPLIED</a></p></details>`;const all=evidenceFigure(s.figures.fit,'All 10 ROIs for the retained Cycle 1','The accepted scene passed every residual-glint and safety test, so its former candidate is now the final retained Cycle 1.','Blue is the applied Cycle 1 result—not a rejected hypothetical curve. Thin lines are individual ROIs and thick lines are medians.');return `<div class="card"><h2>6. Confirmed residual component and retained Cycle 1</h2><p><b>Conclusion:</b> residual glint was confirmed and Cycle 1 was applied.</p><label><b>Graph view</b> <select onchange="document.getElementById('fitMedian').style.display=this.value==='median'?'block':'none';document.getElementById('fitAll').style.display=this.value==='all'?'block':'none'"><option value="median" selected>Group medians</option><option value="all">All 10 ROIs</option></select></label></div><div id="fitMedian">${median}</div><div id="fitAll" style="display:none">${all}</div>`}
function gateExplanation(s){const e=s.evidence;const tests=[
['Controlled known-glint recovery',e.injectionPass,'Calibration must pass',`Sensitivity ${(100*e.injectionSensitivity).toFixed(1)}%; false-positive rate ${(100*e.zeroFalsePositiveRate).toFixed(1)}%; median k error ${(100*e.medianKRelativeError).toFixed(1)}%`,'Shows that known added glint can be recovered under the controlled test.','lod'],
['LOW-group detections',e.detectedLow<=1,'≤ 1 of 10 ROIs',`${e.detectedLow} of 10`,'False detections should remain uncommon where original glint was weakest.','counts'],
['HIGH-group detections',e.detectedHigh>=5,'≥ 5 of 10 ROIs',`${e.detectedHigh} of 10`,'A real residual should be common where original glint was strongest.','counts'],
['HIGH − LOW additional component',e.highMinusLow>e.detectionLimit,`> ${e.detectionLimit.toFixed(6)}`,e.highMinusLow.toFixed(6),'Tests whether the HIGH group retains more glint-like brightness than LOW. This current cutoff is methodological and needs a dedicated null bootstrap.','highlow'],
['Relationship with original B11/B12',Number.isFinite(e.correlation)&&e.correlation>=.30&&e.correlationP<=.10,'r ≥ 0.30 and p ≤ 0.10',`r = ${e.correlation.toFixed(3)}; p = ${e.correlationP.toFixed(3)}`,'The fitted amount should rise where the original surface-reflection indicator was stronger.','corr'],
['HIGH greater than LOW',e.highGreaterLowP<=.05,'one-sided p ≤ 0.05',`p = ${e.highGreaterLowP.toFixed(3)}`,'Checks whether the LOW–HIGH ordering is unlikely to be random.','pvalue']];
const failed=tests.filter(t=>!t[1]);const rows=tests.map(t=>`<tr><td>${t[0]} ${helpButton(t[5])}</td><td>${t[2]}</td><td>${t[3]}</td><td>${t[4]}</td><td><b style="color:${t[1]?'#047857':'#b91c1c'}">${t[1]?'PASS':'FAIL'}</b></td></tr>`).join('');return `<div class="card ${s.extra?'note':'warn'}"><h2>7. Cycle 1 acceptance decision</h2><p>${s.extra?'All six scene-level tests supported an additional correction, so Cycle 1 was retained.':'Cycle 1 is applied only when all six tests pass. This scene failed '+failed.length+' test'+(failed.length===1?'':'s')+': <b>'+failed.map(t=>t[0]).join(', ')+'</b>. Cycle 0 is therefore retained. This means residual glint was not confidently detectable—not that its true amount is exactly zero.'}</p><table><tr><th>Criterion</th><th>Required value</th><th>Observed value</th><th>Why it matters</th><th>Decision</th></tr>${rows}</table><details><summary><b>Threshold calculation and calibration values</b></summary><table><tr><th>Threshold</th><th>How calculated</th><th>Value used</th></tr><tr><td>Additional-component detection limit ${helpButton('lod')}</td><td>95th percentile of fitted component in 2,500 zero-added-glint trials</td><td>${e.detectionLimit.toFixed(6)} reflectance</td></tr><tr><td>RMSE-improvement limit ${helpButton('rmse')}</td><td>95th percentile of apparent improvement in zero-added-glint trials</td><td>${e.rmseImprovementLimit.toFixed(6)} reflectance</td></tr><tr><td>Minimum relative improvement</td><td>95th percentile of null improvement gain</td><td>${e.improvementGainLimit.toFixed(3)}%</td></tr><tr><td>Spectral-shape similarity ${helpButton('shape')}</td><td>Lower calibrated bound from positive known-glint injections</td><td>${e.shapeSimilarityLimit.toFixed(3)}</td></tr><tr><td>Correlation rule ${helpButton('corr')}</td><td>Predefined scene-level evidence rule</td><td>r ≥ 0.30 and p ≤ 0.10</td></tr><tr><td>HIGH–LOW significance ${helpButton('pvalue')}</td><td>Predefined one-sided group-comparison rule</td><td>p ≤ 0.05</td></tr></table></details></div>`}
function originalGlintEvidence(s){const med=g=>median(s.roi.filter(r=>r.group===g).map(r=>r.rhog));const values=s.roi.map(r=>`<tr><td>${r.id}</td><td>${r.group}</td><td>${r.rhog.toFixed(6)}</td></tr>`).join('');return `<div class="card"><h2>1. Original L2A glint assessment</h2><p><b>Purpose:</b> establish the original surface-reflection pattern before correction. The original B11/B12 indicator ranks the same 30 offshore ROIs from weaker to stronger likely surface reflection. ${helpButton('corr')}</p><div class="status">${metric('LOW median',med('LOW').toFixed(6))}${metric('MEDIUM median',med('MEDIUM').toFixed(6))}${metric('HIGH median',med('HIGH').toFixed(6))}</div><p class="note"><b>Interpretation:</b> the median indicator rises from LOW to HIGH, so the original image contains an ordered offshore surface-reflection pattern consistent with glint. This indicator ranks relative strength; it is not a direct measurement of pure glint.</p><details><summary><b>Show all 30 ROI B11/B12 indicator values</b></summary><table><tr><th>ROI</th><th>Group</th><th>Original indicator</th></tr>${values}</table></details></div>`+evidenceFigure(s.figures.roi_map,'Original ROI and glint-group locations','Shows where the LOW, MEDIUM and HIGH offshore samples are located.','The groups should follow the offshore surface-reflection pattern rather than only island edges or shallow reef structures.')}
function cycle0Evaluation(s){const groups=['LOW','MEDIUM','HIGH'];const gm={};groups.forEach(g=>gm[g]=DATA.bands.map((_,i)=>median(s.roi.filter(r=>r.group===g).map(r=>r.removed0[i]))));const rows=DATA.bands.map((b,i)=>`<tr><td>${b} (${DATA.wavelengths[i]} nm)</td>${groups.map(g=>`<td>${gm[g][i].toFixed(6)}</td>`).join('')}</tr>`).join('');const W=1000,H=500,p={l:90,r:30,t:95,b:65},all=groups.flatMap(g=>gm[g]),lo=0,hi=Math.max(...all)*1.12,X=x=>p.l+(x-DATA.wavelengths[0])/(DATA.wavelengths.at(-1)-DATA.wavelengths[0])*(W-p.l-p.r),Y=y=>H-p.b-(y-lo)/(hi-lo)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/><text x="${W/2}" y="30" text-anchor="middle" font-size="24" font-weight="700">Median reflectance removed by Cycle 0</text>`;groups.forEach((g,i)=>{const x=315+i*155;z+=`<line x1="${x}" x2="${x+38}" y1="66" y2="66" stroke="${colors[g]}" stroke-width="6"/><text x="${x+48}" y="72" font-size="16">${g}</text>`});for(let j=0;j<5;j++){const v=hi*j/4;z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#dbe3ea"/><text x="${p.l-10}" y="${Y(v)+5}" text-anchor="end" font-size="14">${v.toFixed(3)}</text>`}groups.forEach(g=>{const pts=gm[g].map((v,i)=>`${X(DATA.wavelengths[i])},${Y(v)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${colors[g]}" stroke-width="5"/>`});DATA.wavelengths.forEach(w=>z+=`<text x="${X(w)}" y="${H-30}" text-anchor="middle" font-size="14">${w}</text>`);z+=`<text x="${W/2}" y="${H-5}" text-anchor="middle" font-size="17">Wavelength (nm)</text><text transform="translate(22 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle" font-size="17">Removed BOA reflectance</text>`;return `<div class="card"><h2>3. Cycle 0 response and safety evaluation</h2><p><b>Purpose:</b> quantify what the first correction removed and determine whether it produced unsafe negative water values.</p><svg viewBox="0 0 ${W} ${H}" style="display:block;width:100%;height:auto;border:1px solid #94a3b8">${z}</svg><p class="note"><b>Interpretation:</b> each coloured line is the median amount subtracted from one original-glint group. A larger removal in HIGH than LOW shows that Cycle 0 responds more strongly where the original B11/B12 indicator was stronger. This supports the Cycle 0 response, but Section 4 separately tests whether detectable residual glint remains.</p><details><summary><b>Show exact band-by-band values</b></summary><table><tr><th>Band</th><th>LOW removed</th><th>MEDIUM removed</th><th>HIGH removed</th></tr>${rows}</table></details><table><tr><th>Safety criterion</th><th>Required value</th><th>Observed value</th><th>Decision</th></tr><tr><td>Maximum visible negative pixels</td><td>≤ 1%</td><td>${s.qc.negative.toFixed(3)}%</td><td><b>${s.qc.negative<=1?'PASS':'FAIL'}</b></td></tr></table><p><b>Conclusion:</b> ${s.qc.negative<=1?'Cycle 0 removed a measurable surface-related component without widespread negative values. Section 4 determines whether this correction is sufficient.':'Cycle 0 failed the negative-pixel safety criterion.'}</p></div>`}
function hydrolightContext(s){return `<div class="card"><h2>5. HydroLight simulation and water–glint fitting</h2><p><b>Purpose:</b> protect brightness that could plausibly come from real water. HydroLight supplies possible water-only spectra; it neither supplies the observed satellite spectrum nor generates the glint shape.</p><table><tr><th>Model input</th><th>Values represented</th><th>Role</th></tr><tr><td>Chlorophyll-a</td><td>0.05, 0.20 and 0.50 mg m⁻³</td><td>Represents tested phytoplankton absorption/scattering conditions.</td></tr><tr><td>CDOM absorption at 440 nm</td><td>0.01, 0.04 and 0.10 m⁻¹</td><td>Represents tested dissolved-colour absorption.</td></tr><tr><td>NAP/TSM</td><td>0.25, 0.75, 1.50 and 3.00 g m⁻³</td><td>Represents tested particle/turbidity conditions.</td></tr><tr><td>Direct simulations</td><td>36 combinations</td><td>Original HydroLight grid.</td></tr><tr><td>Interpolated library</td><td>588 possible glint-free water spectra</td><td>Candidate water spectra tested for every ROI.</td></tr><tr><td>Controlled geometry</td><td>SZA 20.42°; wind 5 m s⁻¹</td><td>Fixed tested geometry; not proof of every scene’s true conditions.</td></tr></table><div class="formula">For each j = 1…588: Y = W<sub>j</sub> + k<sub>j</sub>G + ε</div><p>For every possible water spectrum W<sub>j</sub>, the calculation fits a non-negative k<sub>j</sub> ${helpButton('k')} and calculates RMSE. The valid pair with the smallest RMSE is retained as the closest model explanation. The candidate for removal is kG. HydroLight water W is never subtracted.</p><p class="note"><b>If none of the 588 spectra fits adequately:</b> the ROI is outside the tested model envelope. It must be flagged as model mismatch and must not be forced into a glint correction.</p></div><div class="card"><h2>Controlled known-glint validation</h2><p>This is a calibration test, not a measurement of the real scene. Known fractions of an ACOLITE glint spectrum are deliberately added to low-glint water, hidden from the fitting calculation, and then estimated.</p><ul><li><b>Horizontal axis:</b> known multiplier deliberately added.</li><li><b>Vertical axis:</b> multiplier recovered by the calculation.</li><li><b>Black dashed line:</b> perfect recovery.</li><li><b>Green points:</b> median recovered multiplier.</li><li><b>Shaded P05–P95 area:</b> repeated-case variability.</li></ul><p class="note"><b>Conclusion:</b> points close to the perfect-recovery line show that the calculation can recover known injected glint under controlled conditions. This does not by itself prove residual glint in a real scene.</p></div>`+evidenceFigure(s.figures.known,'Controlled known-glint calibration result','Provides the full calibration figure used to establish detection performance.','Compare recovered values with the deliberately known values. The real-scene Cycle 1 decision still requires all spatial and spectral evidence tests.')}
function orderedEvidence(s){const e=s.evidence;let h=roiSelectionSection(s);h+=`<div class="card"><h2>3. Original L2A spectra</h2>${spectrumSvg(s,'before','Original L2A group medians')}<p><b>Interpretation:</b> the three curves show the original spectra at locations classified from lower to higher Cycle 0 glint estimates. Small curve differences mean the visible spectral evidence is weak even when the SWIR-derived estimates differ.</p><p class="note"><b>Conclusion:</b> use this graph to describe whether the original spectral ordering is strong, weak or absent; do not treat a small difference as proof by itself.</p></div>`;h+=cycle0Calculation(s);h+=evidencePanelSet(s.figures.before_cycle0_median_panels,'5. Original and Cycle 0 spectra','Each panel compares the same group and the same wavelength scale before and after the first correction.',['LOW group','MEDIUM group','HIGH group'],'A lower Cycle 0 curve shows the change applied to that group. The HIGH panel should generally change more when the original glint estimate was stronger.');h+=highLowSummary(s);h+=cycle0Evaluation(s);h+=cycle0Qc(s);h+=hydrolightContext(s);h+=fitComparison(s,e);h+=detectionLimitSection(s);h+=evidenceFigure(s.figures.residual,'11. Residual-glint evidence','The x-axis is the original Cycle 0 glint estimate for each ROI. The y-axis is the additional component fitted after Cycle 0. The dashed limit separates values that can and cannot be distinguished from calibrated fitting noise.','Residual glint is confirmed only when the detected components also increase toward HIGH, follow the original spatial pattern and have a glint-like spectrum. Complete detections are LOW '+e.detectedLow+'/10, MEDIUM '+e.detectedMedium+'/10 and HIGH '+e.detectedHigh+'/10.');h+=gateExplanation(s);if(s.extra){h+=evidenceFigure(s.figures.spatial,'13. Cycle 1 correction','The confirmed kG component is subtracted from Cycle 0 using the same valid-water mask.','Cycle 1 was applied because every acceptance criterion passed and the correction passed safety QC.');h+=evidenceFigure(s.figures.retest,'14. Final residual assessment','The same ROIs, detector and frozen thresholds are applied to the Cycle 1 result.','Residual glint is no longer detectable under the fixed criteria; this does not mean its true physical amount is exactly zero.')}else{h+=`<div class="card note"><h2>13. Cycle 1 correction</h2><p><b>Interpretation:</b> the fitted kG component did not pass every residual-glint criterion.</p><p><b>Conclusion:</b> Cycle 1 was not applied. Cycle 0 is the final retained product.</p></div><div class="card"><h2>14. Final residual assessment</h2><p><b>Interpretation:</b> no further correction is evaluated as a retained result because Cycle 1 was not authorized.</p><p class="note"><b>Conclusion:</b> residual glint was not detectable under the fixed complete criteria after Cycle 0, so processing stopped at Cycle 0.</p></div>`}document.getElementById('evidenceContent').innerHTML=h}
function orderedEvidence(s){const e=s.evidence,med=g=>median(s.roi.filter(r=>r.group===g).map(r=>r.rhog)),roiRows=[...s.roi].sort((a,b)=>a.rhog-b.rhog).map(r=>`<tr><td>${r.id}</td><td>${r.b11CandidateBlue.toFixed(6)}</td><td>${r.b12CandidateBlue.toFixed(6)}</td><td>${Math.min(r.b11CandidateBlue,r.b12CandidateBlue).toFixed(6)}</td><td>${r.group}</td></tr>`).join('');let h=`<div class="card"><h2>1. Original glint check</h2><p>The original image is checked before correction. Thirty fixed 7 × 7 offshore-water ROIs are used: 10 LOW, 10 MEDIUM and 10 HIGH according to the glint estimate prepared for Cycle 0.</p><img src="${s.figures.roi_map}" alt="Thirty offshore ROI locations" style="display:block;width:100%;height:auto;border:1px solid #94a3b8">${roiRankingSvg(s)}${spectrumSvg(s,'before','Original L2A spectra')}<p><b>Interpretation:</b> larger classification values indicate stronger estimated surface reflection. The original spectra show whether those locations are also systematically brighter.</p><p class="note"><b>Conclusion:</b> the original surface-reflection estimate varies from LOW to HIGH, so Cycle 0 was applied. The visible spectral separation is supporting evidence and may be weak.</p><details><summary><b>Glint estimates used for all ROIs</b></summary><table><tr><th>ROI</th><th>From B11</th><th>From B12</th><th>Smaller estimate</th><th>Group</th></tr>${roiRows}</table></details></div>`;h+=cycle0Calculation(s);h+=`<div class="card"><h2>3. Cycle 0 result</h2><p>Cycle 0 is compared with the original image at exactly the same ROIs and wavelengths.</p></div>`+evidencePanelSet(s.figures.before_cycle0_median_panels,'Original and Cycle 0 spectra','Each panel compares one fixed group before and after the first correction.',['LOW group','MEDIUM group','HIGH group'],'The lower Cycle 0 line shows the change. The numerical HIGH–LOW comparison below states whether the original ordering became smaller.');h+=highLowSummary(s);h+=cycle0Evaluation(s);h+=cycle0Qc(s);h+=`<div class="card"><h2>5. HydroLight residual calculation</h2><p>Cycle 0 is now the observation. Each ROI is compared with 588 possible water-only spectra. For every possible water spectrum, the calculation estimates how much additional glint-shaped signal would be needed.</p><div class="formula">Cycle 0 = possible water + fitted glint-shaped component + unexplained difference</div><p><b>Interpretation:</b> HydroLight protects signal that could be real water. The fitted additional component is only a candidate and is not removed automatically.</p><p class="note"><b>Conclusion:</b> the candidate proceeds to the fixed residual-glint tests below.</p></div>`+fitComparison(s,e);h+=`<div class="card"><h2>6. Residual glint check</h2><p>All required conditions must pass: detectable magnitude, improved spectral fit, glint-like shape, more detections in HIGH than LOW, a positive relationship with the original glint estimate, and HIGH values greater than LOW.</p></div>`+detectionLimitSection(s)+evidenceFigure(s.figures.residual,'Residual-glint results','Left: a rising pattern would mean stronger original-glint locations retain more fitted signal. Right: HIGH should be greater than LOW.','Observed detections are LOW '+e.detectedLow+'/10, MEDIUM '+e.detectedMedium+'/10 and HIGH '+e.detectedHigh+'/10. '+(s.extra?'All required scene conditions passed.':'The complete conditions did not pass; residual glint was not confirmed.'))+gateExplanation(s);if(s.extra){h+=evidenceFigure(s.figures.spatial,'7. Cycle 1 correction','The confirmed additional component is subtracted from Cycle 0.','Cycle 1 was applied because every residual-glint condition passed.');h+=evidenceFigure(s.figures.retest,'8. Final glint check','The same detector, ROIs and limits are applied again to Cycle 1.','Residual glint is no longer detectable under the fixed criteria. Cycle 1 is the final product.')}else{h+=`<div class="card note"><h2>7. Cycle 1 correction</h2><p><b>Interpretation:</b> at least one required residual-glint condition failed.</p><p><b>Conclusion:</b> Cycle 1 was not applied. Processing stopped at Cycle 0.</p></div><div class="card"><h2>8. Final glint check</h2><p><b>Interpretation:</b> Cycle 0 is retained because additional glint was not confirmed strongly enough for safe subtraction.</p><p class="note"><b>Conclusion:</b> no residual glint was detectable under the complete fixed criteria. Final product = Cycle 0.</p></div>`}document.getElementById('evidenceContent').innerHTML=h}
function renderArchive(){const counts={};DATA.archive.forEach(r=>counts[r.category]=(counts[r.category]||0)+1);document.getElementById('archiveSummary').innerHTML=Object.entries(counts).map(([k,v])=>metric(k,v)).join('');document.getElementById('archiveTable').innerHTML='<tr><th>Scene</th><th>Archive outcome</th><th>Reason</th></tr>'+DATA.archive.map(r=>`<tr><td>${r.scene}</td><td><b>${r.category}</b></td><td>${r.reason}</td></tr>`).join('')}
function renderEvidence(s){const e=s.evidence;let h=`<div class="card"><h2>Residual-glint decision for ${s.scene}</h2><p><b>Before</b> = original L2A. <b>Cycle 0</b> = first ACOLITE-style correction. <b>Cycle 1</b> = proposed additional residual correction. There is no “Cycle 2” in this experiment.</p><div class="status">${metric('Residual detections',`${e.detectedLow+e.detectedMedium+e.detectedHigh}/30`)}${metric('LOW / MEDIUM / HIGH',`${e.detectedLow} / ${e.detectedMedium} / ${e.detectedHigh}`)}${metric('Relation with B11/B12',`r = ${e.correlation.toFixed(3)}`)}${metric('Detection limit',e.detectionLimit.toFixed(6))}${metric('Decision',s.extra?'APPLY CYCLE 1':'KEEP CYCLE 0')}</div></div>`;h+=evidencePanelSet(s.figures.before_cycle0_panels,'1. What changed after the first correction?','Shows every offshore ROI spectrum before correction and after Cycle 0.',['LOW ROIs: Before and Cycle 0','MEDIUM ROIs: Before and Cycle 0','HIGH ROIs: Before and Cycle 0'],'Cycle 0 should lower surface-reflection brightness while preserving plausible water-spectrum shapes. This graph alone does not prove that all glint is gone.');h+=evidencePanelSet(s.figures.known_panels,'2. Can the calculation recover glint when the answer is known?','Known glint is deliberately added, hidden from the calculation, then estimated.',['Known water, contaminated spectrum and recovered water','Known added glint versus estimated glint','Band error after removing estimated glint'],'The estimated glint should approach the deliberately added glint, and the recovered spectrum should return toward the known clean spectrum. This establishes the detection capability; it is not a real-scene truth test.');h+=evidenceFigure(s.figures.residual,'3. Is residual glint detected after Cycle 0?','Tests whether the fitted remaining component is above the calibrated limit, glint-shaped, and related to the original B11/B12 surface-reflection pattern.','Residual glint is supported when detections and fitted magnitude increase from LOW toward HIGH original-glint ROIs and follow B11/B12. Here the counts are LOW '+e.detectedLow+', MEDIUM '+e.detectedMedium+', HIGH '+e.detectedHigh+'.');h+=evidencePanelSet(s.figures.fit_panels,'4. What do all HydroLight possibilities and fitted kG contribute?','A separate k is fitted for each of the 588 possible water spectra; no single HydroLight water is assumed beforehand. The plotted water curve is the retained best-supported match for each ROI.',['LOW ROIs: Cycle 0, Cycle 1 candidate and matched water','MEDIUM ROIs: Cycle 0, Cycle 1 candidate and matched water','HIGH ROIs: Cycle 0, Cycle 1 candidate and matched water'],'The removable candidate is kG, not the HydroLight water. HydroLight is a physical possibility library, not the true Tidung answer. Supporting RMSE changes from '+e.rmse0.toFixed(6)+' to '+e.rmse1.toFixed(6)+'.');h+=evidenceFigure(s.figures.spatial,'5. What is the final correction?','Shows where the estimated residual component is removed and the resulting Cycle-1 product.','A valid correction should target the original glint pattern without producing widespread negative pixels or destroying water structure. Final decision: '+(s.extra?'Cycle 1 retained.':'Cycle 1 not authorized; Cycle 0 retained.') );if(s.figures.retest)h+=evidenceFigure(s.figures.retest,'6. After correction, is glint still detectable?','Repeats the same fixed residual detector on the final image.','Success means the final spectra no longer pass the complete residual-glint rule or track the original B11/B12 pattern. It means not detectable above the calibrated limit—not mathematically zero glint.');else h+=`<div class="card warn"><h2>6. Final repeated test</h2><p>No additional correction was retained for this scene, so there is no Cycle-1 success claim. The scientifically retained result remains Cycle 0.</p></div>`;document.getElementById('evidenceContent').innerHTML=h}
function update(){const s=DATA.scenes[current];document.getElementById('status').innerHTML=metric('Scene',s.scene)+metric('Final product',s.retained)+metric('Additional correction',s.extra?'APPLIED':'NOT REQUIRED/AUTHORIZED')+metric('Visible negatives',s.qc.negative.toFixed(3)+'%')+metric('Downstream numeric QC',s.downstream);document.getElementById('decisionText').innerHTML=`<h3>Decision</h3>${s.reason}. ${s.extra?'This scene passed the residual-glint evidence, safety QC and final re-test.':'The first correction was retained because stronger subtraction was not scientifically supported.'}`;maps.forEach((m,i)=>{m.eachLayer(l=>{if(l instanceof L.ImageOverlay)m.removeLayer(l)});const overlay=L.imageOverlay(s.images[['before','cycle0','final'][i]],s.bounds,{opacity:1,interactive:true}).addTo(m);overlay.on('click',()=>openLarge(['before','cycle0','final'][i]));m.fitBounds(s.bounds);m.setZoom(m.getZoom()+1)});document.getElementById('downloads').innerHTML=`<a class="button" target="_blank" href="${s.downloads.boa}">Final BOA folder</a><a class="button" target="_blank" href="${s.downloads.Rrs}">Rrs GeoTIFFs</a><a class="button" target="_blank" href="${s.downloads.rrs}">rrs GeoTIFFs</a><a class="button" target="_blank" href="PIXEL_RRS_EXPORT/XLSX/${s.scene}_pixel_Rrs_rrs.xlsx">Per-pixel Excel</a><a class="button" target="_blank" href="PIXEL_RRS_EXPORT/XLSX/Tidung_pixel_Rrs_rrs_index.xlsx">Excel index</a><a class="button" target="_blank" href="${s.downloads.qc}">Band QC CSV</a>`;document.getElementById('qcTable').innerHTML=`<tr><th>Check</th><th>Result</th><th>Meaning</th></tr><tr><td>Median Rrs B02 / B03 / B04</td><td>${s.qc.RrsB02.toFixed(5)} / ${s.qc.RrsB03.toFixed(5)} / ${s.qc.RrsB04.toFixed(5)} sr⁻¹</td><td>Visible-band central values after masking</td></tr><tr><td>Maximum visible negative pixels</td><td>${s.qc.negative.toFixed(3)}%</td><td>Checks over-correction</td></tr><tr><td>Rrs ↔ rrs round-trip error</td><td>${s.qc.roundtrip.toExponential(2)}</td><td>Checks conversion arithmetic</td></tr><tr><td>Provisional downstream eligibility</td><td><b>${s.downstream}</b></td><td>Numeric readiness only; not field validation</td></tr>`;renderEvidence(s);drawChart()}
function openLarge(stage){const s=DATA.scenes[current],names={before:'Original Sentinel-2 L2A',cycle0:'After first correction',final:'Final retained product'};document.getElementById('lightboxTitle').textContent=`${s.scene} — ${names[stage]}`;document.getElementById('lightboxImage').src=s.images[stage];document.getElementById('lightbox').showModal()}
function median(v){const a=v.filter(Number.isFinite).sort((x,y)=>x-y),n=a.length;return n?a[Math.floor((n-1)/2)]:NaN}
function drawChart(){const svg=document.getElementById('chart'),s=DATA.scenes[current],stage=document.getElementById('stage').value,W=1200,H=520,p={l:85,r:25,t:25,b:65};const vals=s.roi.flatMap(r=>r[stage]).filter(Number.isFinite),y0=Math.min(0,Math.min(...vals)),y1=Math.max(...vals)*1.08;const X=x=>p.l+(x-DATA.wavelengths[0])/(DATA.wavelengths.at(-1)-DATA.wavelengths[0])*(W-p.l-p.r),Y=y=>H-p.b-(y-y0)/(y1-y0)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/>`;for(let j=0;j<5;j++){const y=y0+(y1-y0)*j/4;z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(y)}" y2="${Y(y)}" stroke="#dbe3ea"/><text x="${p.l-12}" y="${Y(y)+5}" text-anchor="end" font-size="15">${y.toFixed(3)}</text>`}DATA.wavelengths.forEach(x=>z+=`<text x="${X(x)}" y="${H-28}" text-anchor="middle" font-size="15">${x}</text>`);for(const r of s.roi){const pts=r[stage].map((y,i)=>`${X(DATA.wavelengths[i])},${Y(y)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${colors[r.group]}" stroke-opacity=".22" stroke-width="2"/>`}for(const g of ['LOW','MEDIUM','HIGH']){const rs=s.roi.filter(r=>r.group===g),m=DATA.wavelengths.map((_,i)=>median(rs.map(r=>r[stage][i]))),pts=m.map((y,i)=>`${X(DATA.wavelengths[i])},${Y(y)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${colors[g]}" stroke-width="5"/>`}z+=`<text x="${(p.l+W-p.r)/2}" y="${H-5}" text-anchor="middle" font-size="18" font-weight="700">Wavelength (nm)</text><text transform="translate(22 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle" font-size="18" font-weight="700">BOA reflectance</text>`;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML=z}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab,.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active');setTimeout(()=>maps.forEach(m=>m.invalidateSize()),20)});document.querySelectorAll('.open-large').forEach(b=>b.onclick=()=>openLarge(b.dataset.image));document.getElementById('closeLightbox').onclick=()=>document.getElementById('lightbox').close();const sel=document.getElementById('sceneSelect');DATA.scenes.forEach((s,i)=>sel.add(new Option(`${s.scene} · ${s.retained}`,i)));sel.onchange=()=>{current=+sel.value;update()};document.getElementById('stage').onchange=drawChart;initMaps();renderArchive();update();
</script></body></html>'''


if __name__ == "__main__":
    main()
