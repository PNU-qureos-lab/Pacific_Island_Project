# Tidung glint-correction processing update

The revised processing workflow uses one shared valid-water mask for Glint-ACOLITE, Hedley, and the B12 baseline. Land/non-water, cloud shadow, medium/high cloud, cirrus, snow/ice, and a 60 m contamination buffer are written as NoData before any estimation or correction.

The archive contains 80 Sentinel-2 Level-2A scenes. Forty passed the project water/contamination gate and were processed; forty were retained in the inventory but excluded from correction.

For every accepted scene, the report structure is: method concepts; Glint-ACOLITE step-by-step products; Hedley step-by-step products; B12 step-by-step products; three-method comparison; HydroLight comparison; and conclusion. Each correction is interpreted using the estimated removed term, corrected BOA/Rrs approximation, negative-pixel diagnostics, residual visible--NIR relationship, and preservation of the low-glint/nearshore controls.

## HydroLight TSM closure

The HydroLight forward closure was rerun from the masked Glint-ACOLITE spectra. TSM is estimated from corrected MSI B04 using the Nechad-2016 calibration, then passed to HydroLight to model a new water spectrum. Thirty-three scenes produced a forward-spectrum closure; seven scenes were excluded because the selected ROI had no valid TSM pixels. This is an optical-closure experiment, not field validation: chlorophyll and CDOM remain declared assumptions, and the satellite product remains Rrs_approx.

