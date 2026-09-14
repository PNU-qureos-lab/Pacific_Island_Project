#!/usr/bin/env python
"""Export one flat per-pixel Rrs/rrs CSV for every retained Tidung scene."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import xy
from rasterio.warp import transform as transform_coords


ROOT = Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
PRODUCTS = ROOT / "FINAL_PRODUCTS"
OUTPUT = ROOT / "PIXEL_RRS_EXPORT"
BANDS = ("B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A")


def band_path(scene: str, folder: str, suffix: str, band: str) -> Path:
    return PRODUCTS / scene / folder / f"{scene}_{band}_{suffix}.tif"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for scene_dir in sorted(p for p in PRODUCTS.iterdir() if p.is_dir()):
        scene = scene_dir.name
        rrs_arrays = []
        sub_arrays = []
        profile = None
        for band in BANDS:
            with rasterio.open(band_path(scene, "02_Rrs_Approx", "Rrs_approx_sr-1", band)) as ds:
                rrs_arrays.append(ds.read(1).astype("float64"))
                if profile is None:
                    profile = {"transform": ds.transform, "crs": ds.crs, "shape": ds.shape}
            with rasterio.open(band_path(scene, "03_rrs_Approx", "rrs_approx_sr-1", band)) as ds:
                sub_arrays.append(ds.read(1).astype("float64"))
        rrs_stack = np.stack(rrs_arrays)
        sub_stack = np.stack(sub_arrays)
        valid = np.all(np.isfinite(rrs_stack), axis=0) & np.all(np.isfinite(sub_stack), axis=0)
        rr, cc = np.where(valid)
        east, north = xy(profile["transform"], rr, cc, offset="center")
        lon, lat = transform_coords(profile["crs"], "EPSG:4326", list(east), list(north))
        out = OUTPUT / f"{scene}_pixel_Rrs_rrs.csv"
        header = ["scene", "pixel_row", "pixel_col", "easting_m", "northing_m", "longitude_deg", "latitude_deg"]
        header += [f"Rrs_{b}_sr-1" for b in BANDS]
        header += [f"rrs_{b}_sr-1" for b in BANDS]
        with out.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for n, (row, col) in enumerate(zip(rr, cc)):
                values = [scene, int(row), int(col), float(east[n]), float(north[n]), float(lon[n]), float(lat[n])]
                values += [float(rrs_stack[i, row, col]) for i in range(len(BANDS))]
                values += [float(sub_stack[i, row, col]) for i in range(len(BANDS))]
                writer.writerow(values)
        manifest.append((scene, len(rr), out.name, str(profile["crs"])))
        print(f"{scene}: {len(rr):,} valid pixels")
    with (OUTPUT / "pixel_export_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scene", "valid_pixel_rows", "csv_file", "source_crs"])
        writer.writerows(manifest)


if __name__ == "__main__":
    main()
