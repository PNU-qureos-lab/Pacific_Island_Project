#!/usr/bin/env python3
"""Portable command-line entry point for the Tidung glint pipeline."""
from __future__ import annotations
import argparse
import importlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

def path(cfg, key):
    value = Path(cfg[key]).expanduser()
    return value if value.is_absolute() else (ROOT / value).resolve()

def configure_experiment(cfg):
    exp = importlib.import_module("run_tidung_full_residual_glint_experiment")
    exp.SCENE = cfg["scene"]
    exp.SOURCE = path(cfg, "comparison_outputs")
    exp.JOINT = path(cfg, "joint_multiband_outputs")
    exp.CONTROL = path(cfg, "controlled_hydrolight_outputs")
    exp.OUT = path(cfg, "experiment_output") / "scenes" / exp.SCENE
    exp.RNG = np.random.default_rng(int(cfg.get("random_seed", 20260911)) + int(exp.SCENE[:8]))
    return exp

def main():
    parser = argparse.ArgumentParser(description="Run the Tidung residual-glint workflow without Codex.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--mode", choices=["one-scene", "all-scenes", "export"], default="one-scene")
    parser.add_argument("--scene", help="Override the scene in config.json")
    args = parser.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.scene:
        cfg["scene"] = args.scene
    if args.mode == "one-scene":
        configure_experiment(cfg).main()
    elif args.mode == "all-scenes":
        exp = configure_experiment(cfg)
        batch = importlib.import_module("run_tidung_all_scenes_residual_glint_experiment")
        batch.experiment = exp
        batch.JOINT = path(cfg, "joint_multiband_outputs")
        batch.OUT = path(cfg, "experiment_output")
        batch.SCENES = sorted(p.name for p in (batch.JOINT / "02_Multiband_Inputs").iterdir() if p.is_dir())
        batch.main()
    else:
        exporter = importlib.import_module("export_tidung_production_products")
        exporter.PROJECT = ROOT
        exporter.SOURCE = path(cfg, "experiment_output")
        exporter.ARCHIVE = path(cfg, "l2a_archive")
        exporter.OUTPUT = path(cfg, "final_product_output")
        exporter.PRODUCTS = exporter.OUTPUT / "FINAL_PRODUCTS"
        exporter.main()

if __name__ == "__main__":
    main()
