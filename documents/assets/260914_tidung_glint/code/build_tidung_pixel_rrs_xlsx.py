#!/usr/bin/env python
"""Build memory-efficient per-scene XLSX files from the pixel CSV exports.

Artifact Tool was attempted first but cannot serialize ~2.6 million cells per
scene within its 4 GB heap.  This fallback uses XlsxWriter constant-memory mode.
"""

from __future__ import annotations

import csv
from pathlib import Path

import xlsxwriter


ROOT = Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913\PIXEL_RRS_EXPORT")
OUTPUT = ROOT / "XLSX"


def write_scene(csv_path: Path) -> tuple[str, int, str]:
    scene = csv_path.name[:12]
    out = OUTPUT / f"{scene}_pixel_Rrs_rrs.xlsx"
    workbook = xlsxwriter.Workbook(out, {"constant_memory": True, "nan_inf_to_errors": True})
    pixels = workbook.add_worksheet("Pixel spectra")
    notes = workbook.add_worksheet("Read me")
    header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78", "text_wrap": True})
    number = workbook.add_format({"num_format": "0.00000000"})
    integer = workbook.add_format({"num_format": "0"})
    coordinate = workbook.add_format({"num_format": "0.000000"})
    pixels.hide_gridlines(2)
    pixels.freeze_panes(1, 0)
    pixels.set_column("A:A", 16)
    pixels.set_column("B:C", 11)
    pixels.set_column("D:G", 15)
    pixels.set_column("H:W", 15)
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        for col, value in enumerate(headers):
            pixels.write(0, col, value, header)
        count = 0
        for row_index, row in enumerate(reader, start=1):
            pixels.write_string(row_index, 0, row[0])
            for col in range(1, len(row)):
                fmt = integer if col in (1, 2) else coordinate if col <= 6 else number
                pixels.write_number(row_index, col, float(row[col]), fmt)
            count += 1
    pixels.autofilter(0, 0, count, len(headers) - 1)
    note_rows = [
        ("Scene", scene),
        ("One row", "One valid georeferenced pixel"),
        ("Rrs columns", "Approximate above-surface Rrs = final retained BOA reflectance / pi"),
        ("rrs columns", "Approximate below-surface rrs = Rrs / (0.52 + 1.7 Rrs)"),
        ("Units", "sr-1"),
        ("Coordinates", "Projected pixel-centre coordinates and EPSG:4326 longitude/latitude"),
        ("Radiometric limitation", "Derived from Sen2Cor L2A BOA reflectance; not field-validated water-leaving reflectance"),
        ("IOP limitation", "Absorption a and backscattering bb are not included; retrieve them with a documented semi-analytical inversion"),
    ]
    notes.hide_gridlines(2)
    notes.set_column("A:A", 24)
    notes.set_column("B:B", 100)
    for row, (label, value) in enumerate(note_rows):
        notes.write(row, 0, label, header if row == 0 else None)
        notes.write(row, 1, value, header if row == 0 else None)
    workbook.close()
    return scene, count, out.name


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(ROOT.glob("*_pixel_Rrs_rrs.csv")):
        result = write_scene(path)
        results.append(result)
        print(f"{result[0]}: {result[1]:,} rows")
    index = OUTPUT / "Tidung_pixel_Rrs_rrs_index.xlsx"
    workbook = xlsxwriter.Workbook(index)
    sheet = workbook.add_worksheet("Scene index")
    header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78"})
    headings = ["Scene", "Valid pixel rows", "Workbook", "Contents"]
    for col, value in enumerate(headings):
        sheet.write(0, col, value, header)
    for row, (scene, count, filename) in enumerate(results, start=1):
        sheet.write_string(row, 0, scene)
        sheet.write_number(row, 1, count)
        sheet.write_url(row, 2, f"external:{filename}", string=filename)
        sheet.write_string(row, 3, "Pixel coordinates, 8 Rrs bands and 8 rrs bands")
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, len(results), 3)
    sheet.set_column("A:A", 18)
    sheet.set_column("B:B", 18)
    sheet.set_column("C:C", 38)
    sheet.set_column("D:D", 55)
    workbook.close()
    print(f"Created {len(results)} scene workbooks and index")


if __name__ == "__main__":
    main()
