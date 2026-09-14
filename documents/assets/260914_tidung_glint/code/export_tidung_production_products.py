#!/usr/bin/env python
"""Export retained Tidung glint products, Rrs_approx, and rrs_approx.

This packaging stage does not re-decide the residual-glint experiment. It uses
the frozen all-scene decisions and final retained rasters, keeps every rejected
scene in the master inventory, and records all L2A SAFE products in the archive.
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio


PROJECT = Path(r"C:\Users\phili\Documents\ChatGPT\ACOLITE-Glint Correction")
SOURCE = PROJECT / "outputs" / "Tidung_Full_Glint_All_Scenes_Experiment_20260911"
ARCHIVE = Path(r"H:\Sentinel-2\Tidung\L2A")
OUTPUT = Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
PRODUCTS = OUTPUT / "FINAL_PRODUCTS"
BANDS = ("B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def archive_key(name: str) -> str:
    match = re.match(r"(S2[ABC])_MSIL2A_(\d{8})", name)
    if not match:
        return name
    return f"{match.group(2)}_{match.group(1)}"


def write_tif(path: Path, array: np.ndarray, profile: dict, description: str, unit: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    out_profile.update(
        driver="GTiff", count=1, dtype="float32", nodata=np.nan,
        compress="deflate", predictor=3, tiled=True, blockxsize=256, blockysize=256,
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(array.astype("float32"), 1)
        dst.set_band_description(1, description)
        dst.update_tags(
            AREA_OR_POINT="Area", quantity=description, unit=unit,
            source="Sentinel-2 Sen2Cor L2A BOA; final retained glint-correction experiment product",
        )


def product_qc(scene: str, band: str, boa: np.ndarray, rrs: np.ndarray, sub: np.ndarray) -> dict:
    valid = np.isfinite(boa)
    values_boa = boa[valid]
    values_rrs = rrs[valid]
    values_sub = sub[valid]
    reconstructed = 0.52 * values_sub / (1.0 - 1.7 * values_sub)
    roundtrip = float(np.nanmax(np.abs(reconstructed - values_rrs))) if values_rrs.size else math.nan
    return {
        "scene": scene,
        "band": band,
        "valid_pixels": int(valid.sum()),
        "BOA_p01": float(np.nanpercentile(values_boa, 1)) if values_boa.size else math.nan,
        "BOA_median": float(np.nanmedian(values_boa)) if values_boa.size else math.nan,
        "BOA_p99": float(np.nanpercentile(values_boa, 99)) if values_boa.size else math.nan,
        "above_surface_Rrs_p01_sr-1": float(np.nanpercentile(values_rrs, 1)) if values_rrs.size else math.nan,
        "above_surface_Rrs_median_sr-1": float(np.nanmedian(values_rrs)) if values_rrs.size else math.nan,
        "above_surface_Rrs_p99_sr-1": float(np.nanpercentile(values_rrs, 99)) if values_rrs.size else math.nan,
        "below_surface_rrs_p01_sr-1": float(np.nanpercentile(values_sub, 1)) if values_sub.size else math.nan,
        "below_surface_rrs_median_sr-1": float(np.nanmedian(values_sub)) if values_sub.size else math.nan,
        "below_surface_rrs_p99_sr-1": float(np.nanpercentile(values_sub, 99)) if values_sub.size else math.nan,
        "negative_percent": float(100 * np.mean(values_rrs < 0)) if values_rrs.size else math.nan,
        "nonfinite_conversion_pixels": int(np.sum(~np.isfinite(values_sub))),
        "Rrs_rrs_roundtrip_max_abs_error": roundtrip,
        "numeric_conversion_pass": bool(values_rrs.size and np.isfinite(roundtrip) and roundtrip < 1e-6),
    }


def main() -> None:
    if not ARCHIVE.exists() or not SOURCE.exists():
        raise FileNotFoundError("Required L2A archive or experiment output is missing")
    PRODUCTS.mkdir(parents=True, exist_ok=True)
    statuses = read_csv(SOURCE / "all_33_scene_final_status.csv")
    status_by_scene = {r["scene"]: r for r in statuses}

    archive_rows = []
    for safe in sorted(ARCHIVE.glob("*.SAFE")):
        scene = archive_key(safe.name)
        status = status_by_scene.get(scene)
        archive_rows.append({
            "scene": scene,
            "safe_product": safe.name,
            "archive_path": str(safe),
            "residual_experiment_scope": "YES" if status else "NO",
            "final_decision": status["decision"] if status else "NOT_IN_STRICT_33_SCENE_EXPERIMENT",
            "reason": status["stop_reason"] if status else "Not included in the previously frozen clear-scene candidate set; no final product exported",
        })
    write_csv(OUTPUT / "00_MASTER_QC" / "all_80_L2A_scene_inventory.csv", archive_rows)
    write_csv(OUTPUT / "00_MASTER_QC" / "strict_33_scene_final_decisions.csv", statuses)

    band_qc: list[dict] = []
    product_manifest: list[dict] = []
    retained_summaries: list[dict] = []
    for status in statuses:
        scene = status["scene"]
        if not status["decision"].startswith("RETAIN_"):
            continue
        scene_source = SOURCE / "scenes" / scene
        summary = json.loads((scene_source / "experiment_summary.json").read_text(encoding="utf-8"))
        scene_out = PRODUCTS / scene
        boa_out = scene_out / "01_Final_BOA_Reflectance"
        rrs_out = scene_out / "02_Rrs_Approx"
        sub_out = scene_out / "03_rrs_Approx"
        qc_out = scene_out / "04_QC"
        provenance_out = scene_out / "05_Provenance"
        qc_out.mkdir(parents=True, exist_ok=True)
        provenance_out.mkdir(parents=True, exist_ok=True)

        scene_rows = []
        for band in BANDS:
            src = scene_source / "07_Final_QC" / f"final_retained_{band}.tif"
            if not src.exists():
                raise FileNotFoundError(src)
            with rasterio.open(src) as ds:
                boa = ds.read(1).astype("float64")
                profile = ds.profile
            rrs = boa / math.pi
            sub = rrs / (0.52 + 1.7 * rrs)
            write_tif(boa_out / f"{scene}_{band}_final_BOA_reflectance.tif", boa, profile,
                      f"Final retained BOA reflectance {band}", "dimensionless")
            write_tif(rrs_out / f"{scene}_{band}_Rrs_approx_sr-1.tif", rrs, profile,
                      f"Approximate above-water Rrs {band}", "sr-1")
            write_tif(sub_out / f"{scene}_{band}_rrs_approx_sr-1.tif", sub, profile,
                      f"Approximate below-surface rrs {band}", "sr-1")
            row = product_qc(scene, band, boa, rrs, sub)
            scene_rows.append(row)
            band_qc.append(row)
            for quantity, path in (
                ("BOA_reflectance", boa_out / f"{scene}_{band}_final_BOA_reflectance.tif"),
                ("above_surface_Rrs_approx", rrs_out / f"{scene}_{band}_Rrs_approx_sr-1.tif"),
                ("below_surface_rrs_approx", sub_out / f"{scene}_{band}_rrs_approx_sr-1.tif"),
            ):
                product_manifest.append({"scene": scene, "band": band, "quantity": quantity, "path": str(path)})

        visible = [r for r in scene_rows if r["band"] in ("B02", "B03", "B04")]
        numeric_pass = all(r["numeric_conversion_pass"] for r in scene_rows)
        negative_pass = max(r["negative_percent"] for r in visible) <= 1.0
        medians = [r["above_surface_Rrs_median_sr-1"] for r in visible]
        spectrum_nonzero = bool(np.nanmax(medians) - np.nanmin(medians) > 1e-6)
        downstream_pass = bool(numeric_pass and negative_pass and spectrum_nonzero)
        retained_summaries.append({
            "scene": scene,
            "retained_product": summary["final_qc"]["retained_product"],
            "additional_residual_correction_applied": summary["final_qc"]["retained_product"] == "Cycle1",
            "visible_negative_percent_max": max(r["negative_percent"] for r in visible),
            "numeric_conversion_pass": numeric_pass,
            "visible_spectrum_nonzero_pass": spectrum_nonzero,
            "provisional_downstream_eligibility": "PASS" if downstream_pass else "FAIL",
            "scientific_scope": "Algorithm-ready numeric product; not validated against field Rrs or bathymetry ground truth",
        })
        write_csv(qc_out / "band_value_and_conversion_QC.csv", scene_rows)
        shutil.copy2(scene_source / "experiment_summary.json", provenance_out / "residual_experiment_summary.json")
        for name in ("selected_30_offshore_rois.csv",):
            p = scene_source / "01_Inputs" / name
            if p.exists():
                shutil.copy2(p, provenance_out / name)
        figure = scene_source / "13_Figures" / "06_before_cycle0_final_rgb.png"
        if figure.exists():
            shutil.copy2(figure, qc_out / "before_cycle0_final_RGB.png")
        retest = scene_source / "09_Final_Residual_Retest" / "final_residual_retest_summary.json"
        if retest.exists():
            shutil.copy2(retest, provenance_out / "final_residual_retest_summary.json")

    write_csv(OUTPUT / "00_MASTER_QC" / "retained_scene_downstream_QC.csv", retained_summaries)
    write_csv(OUTPUT / "00_MASTER_QC" / "all_retained_band_value_QC.csv", band_qc)
    write_csv(OUTPUT / "00_MASTER_QC" / "product_manifest.csv", product_manifest)
    write_json(OUTPUT / "00_MASTER_QC" / "package_summary.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "L2A_SAFE_scenes_in_archive": len(archive_rows),
        "strict_candidate_scenes": len(statuses),
        "retained_scenes": len(retained_summaries),
        "rejected_candidate_scenes": sum(r["decision"] == "SCENE_REJECTED" for r in statuses),
        "Cycle1_scenes": [r["scene"] for r in retained_summaries if r["additional_residual_correction_applied"]],
        "provisional_downstream_pass_scenes": sum(r["provisional_downstream_eligibility"] == "PASS" for r in retained_summaries),
        "bands": list(BANDS),
        "above_surface_Rrs_formula": "Rrs_approx = final retained Sen2Cor L2A BOA reflectance / pi",
        "below_surface_rrs_formula": "rrs_approx = Rrs_approx / (0.52 + 1.7 * Rrs_approx)",
        "warning": "These are approximate radiometric transformations of L2A BOA, not field-validated water-leaving Rrs. Do not treat HydroLight as truth.",
    })

    readme = """# Tidung final retained glint-correction products

## What is included

- The archive inventory lists all 80 Sentinel-2 L2A SAFE products.
- The frozen strict experiment evaluated 33 clear-scene candidates.
- Final products are exported only for scientifically retained scenes; rejected scenes remain in the QC tables.
- Eight 20 m bands are provided: B02, B03, B04, B05, B06, B07, B08 and B8A.

## Product definitions

`BOA_reflectance` is the final retained L2A glint-corrected reflectance. `Rrs_approx = BOA / pi` in sr-1. `rrs_approx = Rrs_approx / (0.52 + 1.7 Rrs_approx)` in sr-1.

These Rrs products are explicitly approximate because Sen2Cor L2A BOA is not a dedicated water-leaving reflectance retrieval. Numeric checks confirm finite conversion, round-trip consistency, limited negative visible values and a non-flat visible spectrum. They do not replace field validation. Benthic and bathymetry algorithms should use only pixels passing the supplied masks and should be calibrated/validated independently.

## Residual-glint decision

Cycle 1 is exported only where the known-injection test, 30-ROI residual evidence, image-level safety QC and final residual re-test support it. Otherwise the final retained product is Cycle 0; this means additional residual glint was not demonstrated strongly enough to justify more subtraction.

## Web-map basemaps

Any later HTML viewer should use Esri World Imagery and an Esri default/reference layer. No OpenStreetMap dependency is required.
"""
    (OUTPUT / "README_FINAL_PRODUCTS.md").write_text(readme, encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT), "archive_scenes": len(archive_rows),
        "retained_scenes": len(retained_summaries), "files": len(product_manifest),
    }, indent=2))


if __name__ == "__main__":
    main()
