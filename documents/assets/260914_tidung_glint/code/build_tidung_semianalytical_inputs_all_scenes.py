#!/usr/bin/env python
"""Build deep-water and candidate-shallow masks for all retained Tidung scenes."""
from __future__ import annotations
import contextlib,csv,io,json,sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/"scripts"))
import build_tidung_deep_water_reference as deep
import build_tidung_candidate_shallow_water_mask as shallow

ROOT=Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
FULL=PROJECT/"outputs"/"Tidung_Full_Glint_All_Scenes_Experiment_20260911"
with (FULL/"all_33_scene_final_status.csv").open(newline="",encoding="utf-8-sig") as f:
    scenes=[r["scene"] for r in csv.DictReader(f) if r["decision"].startswith("RETAIN_")]

summary=[]
for scene in scenes:
    print(f"{scene}: deep-water package",flush=True)
    deep.SCENE=scene;deep.PRODUCT=ROOT/"FINAL_PRODUCTS"/scene;deep.OUT=ROOT/"SEMIANALYTICAL_INPUT"/scene/"deep_water"
    with contextlib.redirect_stdout(io.StringIO()):deep.main()
    print(f"{scene}: candidate shallow-water mask",flush=True)
    shallow.SCENE=scene;shallow.OUT=ROOT/"SEMIANALYTICAL_INPUT"/scene;shallow.DEEP=shallow.OUT/"deep_water"/f"{scene}_deep_water_mask.tif"
    with contextlib.redirect_stdout(io.StringIO()):shallow.main()
    d=json.loads((deep.OUT/f"{scene}_deep_water_metadata.json").read_text());s=json.loads((shallow.OUT/f"{scene}_candidate_shallow_water_mask_metadata.json").read_text())
    spectrum=next(csv.DictReader((deep.OUT/f"{scene}_deep_water_Rrs.csv").open(encoding="utf-8-sig")))
    summary.append({"scene":scene,"solar_zenith_deg":d["solar_zenith_deg"],"accepted_deep_ROIs":len(d["accepted_ROI_identifiers"]),"accepted_deep_pixels":d["validation"]["accepted_pixel_count_from_mask"],"deep_reference_confidence":spectrum.get("selection_confidence","STANDARD"),"candidate_shallow_pixels":s["counts"]["candidate_shallow_pixels"],"candidate_shallow_area_km2":s["counts"]["candidate_shallow_pixels"]*0.0004,"deep_shallow_overlap_pixels":s["counts"]["accepted_deep_overlap_pixels"],"status":"PASS"})

out=ROOT/"SEMIANALYTICAL_INPUT"/"all_scene_semianalytical_input_summary.csv"
with out.open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
print(f"Completed {len(summary)} scenes; {out}")
