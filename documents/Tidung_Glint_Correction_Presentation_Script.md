# Presentation script — Sentinel-2 glint correction and HydroLight inverse analysis

This script accompanies the interactive report **Glint Correction — Sentinel-2 L2A — Tidung**. It is written as speaking notes rather than as a second technical report.

## 1. Opening

**Say:**

> This study evaluates glint correction for Sentinel-2 Level-2A imagery around Pulau Tidung. The main method is our transparent Glint-ACOLITE adaptation. Hedley and direct B12 subtraction are included as comparison methods. We retain every intermediate product so that we can see what was removed, where it was removed, and whether the corrected water remains physically reasonable.

> We inventoried 80 Sentinel-2 products. Forty scenes passed the report-screening sequence. Thirty-two scenes contained enough valid water in the primary HydroLight comparison region, ROI-C1, to retain an automatic inverse result.

## 2. What glint is

**Say:**

> A satellite water pixel contains more than water-leaving light. It can also contain atmospheric path radiance and light reflected by the air–water surface. Direct sunlight reflected by wave facets is sun glint. Diffuse skylight reflected by the surface is sky glint. Both add brightness that is not part of the wanted water-leaving signal.

> Bright water alone does not prove glint. Shallow bottom, sediment, haze, cloud and bright-land adjacency can create similar patterns. Therefore, we inspect the image, masks, geometry and spectral behaviour together.

## 3. Data preparation

**Say:**

> Land and non-water pixels are excluded. Sentinel-2 Scene Classification Layer classes for cloud shadow, medium- and high-probability cloud, cirrus and snow or ice are removed, followed by a 60-metre buffer. Excluded pixels become NoData and do not enter fitting, correction or evaluation.

> Stored Sentinel-2 digital numbers are converted to bottom-of-atmosphere, or BOA, reflectance using the product-specific offset and quantification value. The analysis then uses B02, B03 and B04 as the visible output bands, B8 for the Hedley comparison, and B11 and B12 as SWIR references.

## 4. The three glint-correction methods

### 4.1 Glint-ACOLITE

**Say:**

> Glint-ACOLITE uses B11 and B12 to estimate the spatial surface-reflection component. Atmospheric transmittance and Fresnel ratios transfer the selected SWIR reference to B02, B03 and B04. The resulting band-specific glint term is subtracted pixel by pixel.

> The important assumption is that usable water-leaving SWIR reflectance is small compared with the surface-reflection signal. Residual haze, adjacency or real SWIR water signal can therefore contaminate the correction.

### 4.2 Hedley

**Say:**

> Hedley is an empirical method. It fits the relationship between each visible band and B8 inside ROI-A, then removes the B8-correlated component. It is simple and scene-adaptive, but a poor fitting region can remove real variation caused by bottom depth, turbidity or adjacency.

### 4.3 Direct B12 subtraction

**Say:**

> The B12 baseline subtracts the same B12 BOA reference from each visible band. It is transparent and easy to reproduce, but it has no wavelength-specific atmospheric or Fresnel transfer. It can overcorrect if B12 contains haze, adjacency or non-zero water signal.

## 5. How to present the Glint-ACOLITE calculation

**Say:**

> In the report, each calculation step can be opened separately. The panel shows the input, calculation, output, actual selected-date result, interpretation and quality check together.

1. AOT and scene geometry provide the atmospheric and observation inputs.
2. Two-way atmospheric transmittance is calculated for the required Sentinel-2 bands.
3. Fresnel reflectance represents reflection at the air–water interface.
4. B11 and B12 are transferred to a common reference and compared pixel by pixel.
5. The smaller valid candidate becomes the spatial surface-reflection reference, rho-g-reference.
6. The spectral factor K transfers that reference to each visible band.
7. Multiplying the spatial reference by K produces estimated glint for B02, B03 and B04.
8. Estimated glint is subtracted from the original BOA reflectance.
9. Corrected BOA reflectance is divided by pi to form the current Rrs approximation.
10. Original and corrected products are compared on identical display scales.

**Key equations:**

\[
K(\lambda,j)=\frac{t(\lambda)}{t(j)}\frac{F(\lambda)}{F(j)}
\]

\[
\rho_g(\lambda)=\rho_{g,ref}K(\lambda,j)
\]

\[
\rho_{gc}(\lambda)=\rho_{BOA}(\lambda)-\rho_g(\lambda)
\]

\[
R_{rs,approx}(\lambda)=\frac{\rho_{gc}(\lambda)}{\pi}
\]

**Do not say:** “This is field-measured Rrs.”

**Say instead:**

> This is an Rrs approximation derived from Sen2Cor L2A BOA reflectance. It is useful for relative spectral comparison, but absolute validation still requires field measurements.

## 6. Why the first HydroLight comparison was insufficient

**Say:**

> We first compared the corrected satellite spectra with four fixed HydroLight scenarios: pure water, very clear water, clear water and less-clear water. Those scenarios used low or fixed particle concentrations. Their magnitude or blue–green–red shape was often far from the corrected Tidung spectrum.

> This did not automatically mean that the glint correction was wrong. It showed that the original clear-water model assumptions were not sufficient to reproduce the observed spectrum. We therefore added an inverse library search.

## 7. HydroLight inverse calculation — the main explanation

### 7.1 What “inverse” means here

**Say:**

> Forward modelling starts with water properties and predicts a spectrum. Our inverse procedure does the opposite search: it starts with the corrected satellite spectrum and asks which already-simulated HydroLight case is closest.

> It is a discrete lookup-table inversion, not a continuous optimization and not a direct laboratory measurement of TSM.

### 7.2 The target spectrum

**Say:**

> For each date, the primary target is the mean Glint-ACOLITE-corrected B02, B03 and B04 Rrs approximation from ROI-C1. ROI-C2 to ROI-C5 repeat the test in four additional boxes to check spatial consistency. They do not create five different final answers.

### 7.3 Matching the observation conditions

**Say:**

> The HydroLight spectrum is convolved with the spectral response of the matching Sentinel-2 platform—2A, 2B or 2C. The actual scene solar-zenith angle is matched to the nearest simulated angle in the 20, 25, 30, 35 and 40 degree grid.

> Solar-zenith angle is an illumination geometry parameter. It is not TSM and it is not a water-quality score.

### 7.4 The 45 tested candidates

**Say:**

> After platform and solar angle are fixed, we test three predefined water backgrounds. OLI is oligotrophic-clear water, CLR is clear-coastal water, and PRD is productive-coastal water. Each background has a declared chlorophyll-a and CDOM pair.

> Within each background, 15 discrete TSM values are tested. Therefore, each date has three backgrounds times 15 TSM values, which equals 45 candidate spectra.

> Chlorophyll and CDOM were not independently optimized. Wind was fixed at 5 metres per second, and the water was assumed optically deep with no bottom contribution. These assumptions limit the interpretation.

### 7.5 How the closest candidate is selected

For candidate \(c\) and band \(b\):

\[
e_{c,b}=R_{rs,approx}^{satellite}(b)-R_{rs}^{HydroLight}(c,b)
\]

\[
RMSE_c=\sqrt{\frac{e_{c,B02}^{2}+e_{c,B03}^{2}+e_{c,B04}^{2}}{3}}
\]

**Say:**

> We calculate the B02, B03 and B04 residuals for all 45 candidates. Positive residual means the satellite value is higher than HydroLight; negative residual means HydroLight is higher. The candidate with the smallest three-band RMSE is retained as the closest tested case.

> RMSE checks overall magnitude. Spectral angle checks the blue–green–red shape. The individual band residuals show which wavelength still disagrees.

### 7.6 Example result: 25 October 2024

**Say:**

> On 25 October 2024, the actual Sentinel-2A solar-zenith angle was 20.42 degrees, so the 20-degree HydroLight grid was used. ROI-C1 contained 49 valid pixels.

> The smallest-RMSE candidate was the clear-coastal background with TSM 0.5 grams per cubic metre. This background used chlorophyll-a 0.10 milligrams per cubic metre and a-CDOM at 440 nanometres of 0.03 per metre.

> The three-band RMSE was 0.00154 per steradian and the spectral angle was 10.60 degrees. The residuals were plus 0.00047 in B02, minus 0.00058 in B03 and plus 0.00257 per steradian in B04.

> Blue and green were reproduced relatively closely, but the positive red residual remained the largest mismatch. Therefore, the new simulation is a substantial shape improvement over the original low-TSM clear-water reference, but it is not a perfect match.

> All five ROI-C boxes selected the same clear-coastal background and TSM 0.5 grams per cubic metre. Their spectral angles were approximately 9.83 to 10.60 degrees. This supports spatial repeatability for this date, although it is still not field validation.

### 7.7 Result across the retained inverse scenes

**Say:**

> Thirty-two scenes had a valid automatic ROI-C1 inverse result. Eighteen selected the oligotrophic-clear background, 13 selected clear-coastal and one selected productive-coastal.

> Four scenes selected TSM 0.25, 11 selected 0.5, 10 selected 1, five selected 2 and two selected 3 grams per cubic metre. Thus, 21 of 32 scenes selected either 0.5 or 1 gram per cubic metre, which frequently agrees with the range suggested by the professor. This is still a model-fit pattern, not proof of the true TSM.

## 8. What the inverse result does and does not prove

**Say:**

> The inverse result tells us which tested HydroLight spectrum is closest to the Glint-ACOLITE-corrected spectrum under the declared library assumptions. It helps determine whether a plausible water model can reproduce the corrected spectral shape.

> It does not independently prove that Glint-ACOLITE is correct, because Glint-ACOLITE supplies the inversion target. It also does not prove that the selected TSM, chlorophyll or CDOM is the true field concentration.

> A low RMSE can be produced by compensating model assumptions. Residual atmospheric error, bottom influence, adjacency, particle type and incorrect chlorophyll or CDOM can shift the selected TSM.

## 9. How the correction methods are judged

**Say:**

> HydroLight closeness is contextual and is not used as the pass-or-review gate. Each correction method is assessed with four image-based checks.

- **Residual VIS–B8 slope:** how much B8-correlated brightness remains after correction; smaller is better.
- **Negative pixels:** the largest percentage of valid-water visible pixels below zero; a high value warns of over-subtraction.
- **Spatial preservation:** correlation between original and corrected nearshore spatial structure; closer to one is better.
- **Lower-glint change:** mean absolute change in ROI-E; smaller means relatively dark comparison water was altered less.

**Say:**

> No method is declared universally best. A method can remove more brightness but also create negative pixels or destroy real spatial structure. The conclusion is therefore reported separately for every scene.

## 10. Final conclusion

**Say:**

> The study provides an auditable glint-correction chain rather than only a corrected RGB image. Glint-ACOLITE, Hedley and B12 subtraction have different trade-offs, and the most defensible choice depends on the selected date.

> The new HydroLight inversion resolves the main problem in the original comparison: the fixed very-clear-water assumptions were often too low or had the wrong shape. For the 25 October 2024 example, the clear-coastal TSM 0.5 simulation closely reproduces blue and green but retains a red-band mismatch.

> The next validation step is a matched field dataset: above-water or in-water spectral measurements together with gravimetric TSM, chlorophyll-a and CDOM samples collected close to the Sentinel-2 acquisition time. A radiometrically corrected UAV RedEdge product can support spatial comparison, but it does not replace water sampling and field spectroscopy for absolute validation.

## Short answers for likely questions

### “Did you retrieve the true TSM of Tidung?”

> No. We selected the TSM label of the closest tested HydroLight simulation. It is a model-based estimate that requires field validation.

### “Why are there many inverse results?”

> Each eligible date is inverted separately, and five ROI-C boxes test spatial repeatability. The main per-date result is ROI-C1; ROI-C2 to ROI-C5 are supporting checks.

### “Why were 45 candidates tested?”

> The nearest SZA and matching Sentinel-2 platform were fixed first. We then tested three water backgrounds and 15 TSM values within each background: 3 × 15 = 45.

### “Why not select the spectrum with the closest-looking graph?”

> The selection uses the numerical minimum three-band RMSE. Spectral angle and band residuals are then inspected to identify shape and wavelength-specific mismatch.

### “Can UAV RedEdge validate this result?”

> After radiometric calibration and empirical-line correction, UAV data can provide valuable high-resolution spatial comparison. However, airborne reflectance alone is not a direct gravimetric TSM measurement and does not replace matched field spectra and water samples.

### “What is the main limitation?”

> The HydroLight inverse target comes from Glint-ACOLITE, so the model comparison is not independent validation. The lookup table also fixes wind, depth and bottom conditions and searches paired chlorophyll/CDOM backgrounds rather than retrieving every constituent independently.

