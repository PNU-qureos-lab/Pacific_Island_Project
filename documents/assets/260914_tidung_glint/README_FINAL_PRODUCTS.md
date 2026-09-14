# Tidung final retained glint-correction products

## What is included

- The archive inventory lists all 80 Sentinel-2 L2A SAFE products.
- The frozen strict experiment evaluated 33 clear-scene candidates.
- Final products are exported only for scientifically retained scenes; rejected scenes remain in the QC tables.
- Nine bands are provided on the same 20 m grid: B01, B02, B03, B04, B05, B06, B07, B08 and B8A.
- B01 is resampled from its native 60 m resolution. Its pixels align with the 20 m products, but resampling does not create true 20 m spatial information.

## Product definitions

`BOA_reflectance` is the final retained L2A glint-corrected reflectance. `Rrs_approx = BOA / pi` in sr-1. `rrs_approx = Rrs_approx / (0.52 + 1.7 Rrs_approx)` in sr-1.

These Rrs products are explicitly approximate because Sen2Cor L2A BOA is not a dedicated water-leaving reflectance retrieval. Numeric checks confirm finite conversion, round-trip consistency, limited negative visible values and a non-flat visible spectrum. They do not replace field validation. Benthic and bathymetry algorithms should use only pixels passing the supplied masks and should be calibrated/validated independently.

For four-band inversion, use above-surface `Rrs_approx` from B01, B02, B03 and B04 at nominal 443, 492, 560 and 665 nm. B01 uses the same B11/B12 reference selection as Cycle 0 with a scene-specific ACOLITE optical transfer factor. For the retained Cycle-1 scene, its B01 additional correction uses the already accepted spatial Cycle-1 multiplier reconstructed from B02.

## Residual-glint decision

Cycle 1 is exported only where the known-injection test, 30-ROI residual evidence, image-level safety QC and final residual re-test support it. Otherwise the final retained product is Cycle 0; this means additional residual glint was not demonstrated strongly enough to justify more subtraction.

## Web-map basemaps

Any later HTML viewer should use Esri World Imagery and an Esri default/reference layer. No OpenStreetMap dependency is required.
