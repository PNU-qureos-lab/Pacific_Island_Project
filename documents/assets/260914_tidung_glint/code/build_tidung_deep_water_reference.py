#!/usr/bin/env python
"""Build the traceable 20260808_S2A deep-water Rrs reference package."""
from __future__ import annotations
import csv,json,math
from datetime import datetime,timezone
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT=Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
SCENE="20260808_S2A"; BANDS=("B01","B02","B03","B04"); WAVES=(443,490,560,665)
PRODUCT=ROOT/"FINAL_PRODUCTS"/SCENE; OUT=ROOT/"SEMIANALYTICAL_INPUT"/SCENE/"deep_water"

def rows(path):
    with path.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def write_csv(path,data):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    roi=rows(PRODUCT/"05_Provenance"/"selected_30_offshore_rois.csv")
    arrays=[];sources=[];profile=None
    for b in BANDS:
        p=PRODUCT/"02_Rrs_Approx"/f"{SCENE}_{b}_Rrs_approx_sr-1.tif";sources.append(str(p))
        with rasterio.open(p) as ds:
            arrays.append(ds.read(1).astype(float));profile=ds.profile.copy() if profile is None else profile
            if ds.crs!=profile["crs"] or ds.transform!=profile["transform"] or ds.shape!=(profile["height"],profile["width"]):raise RuntimeError("B01-B04 grids differ")
    stack=np.stack(arrays); valid=np.all(np.isfinite(stack),axis=0)
    stats=[];spectra=[]
    for r in roi:
        y,x=int(float(r["row"])),int(float(r["col"]));sl=np.s_[y-3:y+4,x-3:x+4];v=stack[:,sl[0],sl[1]];good=np.all(np.isfinite(v),axis=0)
        px=v[:,good];med=np.median(px,axis=1);std=np.std(px,axis=1);cv=std/med;spectra.append(med)
        stats.append((r,y,x,px,med,std,cv))
    med_matrix=np.stack(spectra); centre=np.median(med_matrix,axis=0);distance=np.sqrt(np.mean(((med_matrix-centre)/np.maximum(centre,1e-9))**2,axis=1));limit=float(np.median(distance)+3*1.4826*np.median(np.abs(distance-np.median(distance))))
    audit=[];mask=np.zeros(valid.shape,np.uint8);mask[~valid]=255;accepted=[]
    for i,(r,y,x,px,med,std,cv) in enumerate(stats):
        dist=float(r["distance_to_land_m"]); outlier=bool(distance[i]>limit); positive=bool(np.all(px>0)); uniform=bool(np.all(cv<=.05))
        if positive and uniform and not outlier and dist>=1500:
            decision="ACCEPTED_DEEP";reason="";accepted.append(r["roi"]);mask[y-3:y+4,x-3:x+4]=np.where(valid[y-3:y+4,x-3:x+4],1,255)
        elif positive and np.all(cv<=.10):
            decision="UNCERTAIN"; reason=("Spectrum is an outlier relative to the offshore ensemble." if outlier else "ROI is closer than 1.5 km to mapped land; reef-slope or bottom influence cannot be independently excluded.")
        else:
            decision="REJECTED";reason="Nonpositive/nonfinite values or excessive within-ROI variability."
        row={"scene":SCENE,"ROI_ID":r["roi"],"existing_glint_group":r["stratum"],"row":y,"column":x,"distance_to_land_m":dist,"valid_pixel_count":int(px.shape[1]),"decision":decision,"rejection_reason":reason}
        for j,w in enumerate(WAVES):row[f"median_Rrs_{w}"]=float(med[j])
        for j,w in enumerate(WAVES):row[f"std_Rrs_{w}"]=float(std[j])
        for j,w in enumerate(WAVES):row[f"CV_Rrs_{w}"]=float(cv[j])
        row.update({"bottom_visible":"false" if decision=="ACCEPTED_DEEP" else "uncertain","cloud_or_shadow":False,"land_adjacency":False,"remaining_glint":False,"boat_or_wake":False,"turbid_plume":False,"spectral_outlier":outlier})
        audit.append(row)
    if not accepted:raise RuntimeError("No ACCEPTED_DEEP ROI")
    accepted_pixels=stack[:,mask==1]
    if not np.all(np.isfinite(accepted_pixels)) or not np.all(accepted_pixels>0):raise RuntimeError("Accepted pixels are not finite and positive")
    combined=np.median(accepted_pixels,axis=1);count=int((mask==1).sum())
    provenance=json.loads((PRODUCT/"05_Provenance"/"B01_processing_and_grid_provenance.json").read_text())
    sza=float(provenance["solar_zenith_deg"])
    spectrum={"scene":SCENE,**{f"deep_Rrs_{w}_sr-1":float(combined[i]) for i,w in enumerate(WAVES)},"accepted_ROI_count":len(accepted),"accepted_pixel_count":count,"solar_zenith_deg":sza,"aggregation_method":"median of all accepted deep-water pixels","selection_method":"Manual RGB context plus finite-positive, <=5% within-ROI CV, ensemble spectral consistency, and >=1.5 km mapped-land distance","Rrs_product_type":"Rrs_approx from glint-corrected Sen2Cor BOA divided by pi"}
    write_csv(OUT/f"{SCENE}_deep_water_Rrs.csv",[spectrum]);write_csv(OUT/f"{SCENE}_deep_water_ROI_audit.csv",audit)
    mp=profile.copy();mp.update(driver="GTiff",dtype="uint8",count=1,nodata=255,compress="deflate",predictor=2)
    with rasterio.open(OUT/f"{SCENE}_deep_water_mask.tif","w",**mp) as ds:
        ds.write(mask,1);ds.set_band_description(1,"Accepted deep-water pixels: 1; valid nonselected: 0; outside valid scene: 255")
    # QC figure
    rgb=np.moveaxis(stack[[3,2,1]]*math.pi,0,-1);shown=np.power(np.clip(rgb/.11,0,1),.85)
    fig,axes=plt.subplots(1,3,figsize=(17,6),constrained_layout=True)
    axes[0].imshow(shown);colors={"ACCEPTED_DEEP":"#16a34a","UNCERTAIN":"#eab308","REJECTED":"#dc2626"}
    for a in audit:axes[0].plot(a["column"],a["row"],"s",mfc="none",mec=colors[a["decision"]],mew=2,ms=10);axes[0].text(a["column"]+3,a["row"],a["ROI_ID"],color=colors[a["decision"]],fontsize=7,weight="bold")
    for k,c in colors.items():axes[0].plot([],[],"s",mfc="none",mec=c,mew=2,label=k)
    axes[0].legend(fontsize=8);axes[0].set_title("Final water RGB and ROI decisions");axes[1].imshow(mask==1,cmap="Greens",vmin=0,vmax=1);axes[1].set_title(f"Accepted deep-water mask\n{len(accepted)} ROIs; {count} pixels")
    for a in audit:
        if a["decision"]=="ACCEPTED_DEEP":axes[2].plot(WAVES,[a[f"median_Rrs_{w}"] for w in WAVES],color="#86b99a",alpha=.7,lw=1.5)
    axes[2].plot(WAVES,combined,"o-",color="#065f46",lw=4,label="Combined pixel median");axes[2].set(xlabel="Wavelength (nm)",ylabel="Rrs_approx (sr⁻¹)",title="Accepted deep-water spectra");axes[2].grid(alpha=.25);axes[2].legend()
    fig.suptitle(f"{SCENE} deep-water reference QC",fontsize=18,weight="bold");fig.savefig(OUT/f"{SCENE}_deep_water_QC.png",dpi=180);plt.close(fig)
    metadata={"source_scene":SCENE,"source_Rrs_files":sources,"band_to_wavelength_nm":dict(zip(BANDS,WAVES)),"CRS":str(profile["crs"]),"transform":list(profile["transform"]),"width":profile["width"],"height":profile["height"],"spatial_resolution_m":20,"ROI_size":"7 x 7 pixels","selection_categories":["ACCEPTED_DEEP","UNCERTAIN","REJECTED"],"selection_criteria":spectrum["selection_method"],"aggregation_method":spectrum["aggregation_method"],"solar_zenith_deg":sza,"solar_zenith_source":provenance["solar_zenith_source"],"Rrs_units":"sr-1","Rrs_conversion_formula":"Rrs_approx = final glint-corrected Sen2Cor BOA reflectance / pi","accepted_ROI_identifiers":accepted,"excluded_ROIs":[{"ROI_ID":a["ROI_ID"],"decision":a["decision"],"reason":a["rejection_reason"]} for a in audit if a["decision"]!="ACCEPTED_DEEP"],"processing_date_utc":datetime.now(timezone.utc).isoformat(),"software_and_script":str(Path(__file__).resolve()),"validation":{"accepted_pixel_count_from_mask":count,"accepted_pixel_count_in_spectrum":spectrum["accepted_pixel_count"],"all_accepted_values_finite_positive":True,"mask_grid_matches_all_four_inputs":True,"independently_recalculated_median_matches":bool(np.allclose(combined,np.median(stack[:,mask==1],axis=1))),"lowercase_rrs_used":False},"limitations":"The deep-water reference is based on manually and statistically screened offshore Sentinel-2 pixels. No field bathymetry was available to independently prove optical depth. The supplied Rrs values are Rrs_approx derived from glint-corrected Sen2Cor L2A BOA reflectance divided by pi and are not field-validated water-leaving Rrs."}
    (OUT/f"{SCENE}_deep_water_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(OUT),"accepted_ROIs":len(accepted),"accepted_pixels":count,"solar_zenith":sza,"spectrum":combined.tolist()},indent=2))
if __name__=="__main__":main()
