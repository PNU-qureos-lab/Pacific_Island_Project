# Tidung Sentinel-2 L2A residual-glint pipeline

Portable Python delivery of the validation-gated Tidung glint experiment. Large
satellite rasters and HydroLight tables are not
stored in the repository; their locations are supplied in `config.json`.

## Scientific scope

- Input: prepared Sentinel-2 L2A BOA bands, water/land masks, B11/B12-derived
  surface-reflection products, and the tested HydroLight water library.
- Cycle 0: the existing ACOLITE-style correction.
- Residual test: known-glint sensitivity calibration plus 30 offshore ROI tests.
- Cycle 1: created only when the frozen residual-evidence gates pass.
- Output: final retained BOA products. The separate export mode produces
  `Rrs_approx = BOA/pi` and below-surface `rrs_approx` with numeric QC.
- Limitation: “not detected” means below the calibrated detector limit, not
  proof of physically zero glint or field validation.

## Installation with Conda (recommended)

```bash
conda env create -f environment.yml
conda activate tidung-glint
```

Alternative:

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -r requirements.txt
```

On Linux/macOS, activate with `source .venv/bin/activate`.

## Configuration

```bash
copy config.example.json config.json
```

Edit every path in `config.json`. Paths may be absolute or relative to this
repository. `config.json` is ignored by Git so local paths are not published.

Validate before running:

```bash
python validate_setup.py config.json
```

## Run

Desktop interface:

```bash
python gui.py
```

The GUI validates the selected configuration, runs one scene, all scenes or
the product export, shows the processing log, and opens the output folder or
generated HTML report. Expected products are final BOA, Rrs and rrs GeoTIFFs,
per-pixel tables, ROI spectra, decisions, QC files, figures and the report.

Command line:

One scene:

```bash
python run_pipeline.py --config config.json --mode one-scene --scene 20240925_S2A
```

All prepared scenes:

```bash
python run_pipeline.py --config config.json --mode all-scenes
```

Export retained BOA, Rrs and rrs products after the batch decisions exist:

```bash
python run_pipeline.py --config config.json --mode export
```

## Repository layout

```text
Tidung_Glint_Pipeline/
  README.md
  LICENSE
  environment.yml
  requirements.txt
  config.example.json
  validate_setup.py
  gui.py
  run_pipeline.py
  run_windows.bat
  scripts/
    run_tidung_controlled_hydrolight_glint_validation.py
    run_tidung_full_residual_glint_experiment.py
    run_tidung_all_scenes_residual_glint_experiment.py
    summarize_tidung_full_glint_batch.py
    export_tidung_production_products.py
    build_tidung_final_products_html.py
```

## Input contract

The processing scripts expect the same validated folder structure used by this
delivery. In particular, `joint_multiband_outputs` must contain
`02_Multiband_Inputs/<SCENE>` and `03_Glint_ACOLITE_Cycle0/<SCENE>`;
`comparison_outputs` must contain masks, B11/B12 reference products, and the
Hedley/B12 comparison outputs; `controlled_hydrolight_outputs` must contain the
HydroLight training library. Run `validate_setup.py` before computation.

## Reproducibility notes

- Random seeds are fixed in `config.json` and made scene-specific.
- Thresholds are calibrated by the controlled known-glint experiment.
- Rejected scenes remain recorded; the workflow does not force Cycle 1.
- Do not publish the repository until the owner replaces `LICENSE` with the
  intended project license and confirms data redistribution permissions.
