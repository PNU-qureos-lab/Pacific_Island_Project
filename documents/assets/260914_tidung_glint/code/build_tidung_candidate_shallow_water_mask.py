#!/usr/bin/env python
"""Build a conservative candidate shallow-water mask for 20260808_S2A."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from scipy.ndimage import distance_transform_edt,uniform_filter,binary_opening,binary_closing,label

ROOT=Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
L2A=Path(r"H:\Sentinel-2\Tidung\L2A");SCENE="20260808_S2A"
OUT=ROOT/"SEMIANALYTICAL_INPUT"/SCENE;DEEP=OUT/"deep_water"/f"{SCENE}_deep_water_mask.tif"
BANDS=("B01","B02","B03","B04");WAVES=(443,490,560,665)

def main():
    arrays=[];profile=None;sources=[]
    for b in BANDS:
        p=ROOT/"FINAL_PRODUCTS"/SCENE/"02_Rrs_Approx"/f"{SCENE}_{b}_Rrs_approx_sr-1.tif";sources.append(str(p))
        with rasterio.open(p) as ds:
            arrays.append(ds.read(1).astype(float));profile=ds.profile.copy() if profile is None else profile
    stack=np.stack(arrays);valid=np.all(np.isfinite(stack),axis=0)&np.all(stack>0,axis=0)
    platform=SCENE.split("_")[1]
    scl_path=next(L2A.glob(f"{platform}_MSIL2A_{SCENE[:8]}*.SAFE/GRANULE/*/IMG_DATA/R20m/*_SCL_20m.jp2"))
    scl=np.zeros(valid.shape,np.uint8)
    with rasterio.open(scl_path) as src:
        reproject(rasterio.band(src,1),scl,src_transform=src.transform,src_crs=src.crs,dst_transform=profile["transform"],dst_crs=profile["crs"],resampling=Resampling.nearest)
    water=scl==6;invalid_class=np.isin(scl,(0,1,3,8,9,10,11));land=np.isin(scl,(4,5))
    complete_water=uniform_filter(water.astype(float),7,mode="constant")>.999
    distance_m=distance_transform_edt(~land)*20
    near_island=(distance_m>=80)&(distance_m<=500)
    with rasterio.open(DEEP) as ds:deep=ds.read(1)==1
    deep_pixels=stack[:,deep]
    deep_median=np.median(deep_pixels,axis=1);deep_mad=1.4826*np.median(np.abs(deep_pixels-deep_median[:,None]),axis=1)
    deep_mad=np.maximum(deep_mad,1e-5)
    score=np.sqrt(np.mean(((stack-deep_median[:,None,None])/deep_mad[:,None,None])**2,axis=0))
    deep_score=np.sqrt(np.mean(((deep_pixels-deep_median[:,None])/deep_mad[:,None])**2,axis=0))
    bottom_threshold=float(np.percentile(deep_score,99))
    visible=np.mean(stack[1:4],axis=0);mean=uniform_filter(np.nan_to_num(visible,nan=0),5,mode="nearest");mean2=uniform_filter(np.nan_to_num(visible*visible,nan=0),5,mode="nearest")
    local_cv=np.sqrt(np.maximum(mean2-mean*mean,0))/np.maximum(mean,1e-8)
    candidate=valid&water&~invalid_class&complete_water&near_island&~deep&(score>bottom_threshold)&(local_cv<=.20)
    candidate=binary_opening(candidate,structure=np.ones((2,2),bool));candidate=binary_closing(candidate,structure=np.ones((3,3),bool))
    # Remove isolated fragments smaller than four 20 m pixels.
    labs,n=label(candidate)
    for i in range(1,n+1):
        if np.sum(labs==i)<4:candidate[labs==i]=False
    mask=np.zeros(valid.shape,np.uint8);mask[~valid|~water|invalid_class]=255;mask[candidate]=1
    out_path=OUT/f"{SCENE}_candidate_shallow_water_mask.tif";p=profile.copy();p.update(driver="GTiff",dtype="uint8",count=1,nodata=255,compress="deflate",predictor=2)
    with rasterio.open(out_path,"w",**p) as ds:
        ds.write(mask,1);ds.set_band_description(1,"Candidate shallow-water benthic inversion mask: 1 run; 0 excluded water; 255 invalid/land/cloud")
        ds.update_tags(AREA_OR_POINT="Area",meaning="1=candidate shallow water; 0=excluded valid water; 255=land/cloud/shadow/invalid")
    metadata={"scene":SCENE,"output":str(out_path),"source_Rrs":sources,"source_SCL":str(scl_path),"source_deep_water_mask":str(DEEP),"grid":{"crs":str(profile["crs"]),"resolution_m":20,"width":profile["width"],"height":profile["height"],"transform":list(profile["transform"])},"mask_values":{"1":"candidate shallow water where benthic inversion may run","0":"valid water excluded from benthic inversion","255":"NoData: land, cloud, shadow or invalid observation"},"rules":{"SCL_water_class":6,"complete_water_neighborhood":"7 x 7 pixels","distance_from_mapped_land_m":[80,500],"all_B01_B04_positive_finite":True,"accepted_deep_water_excluded":True,"detectable_bottom_influence":f"four-band robust distance from deep-water median > deep-water 99th percentile ({bottom_threshold:.6f})","local_visible_CV_max":0.20,"minimum_connected_component_pixels":4},"counts":{"candidate_shallow_pixels":int(candidate.sum()),"excluded_valid_water_pixels":int(((mask==0)&valid).sum()),"nodata_pixels":int((mask==255).sum()),"accepted_deep_overlap_pixels":int(np.sum(candidate&deep))},"limitations":["Candidate mask, not field-validated bathymetry or proof of bottom visibility.","Distance-to-land is used as a reef-platform proxy because field bathymetry is unavailable.","Spectral separation from deep water can also reflect water-mass or turbidity differences; local homogeneity screening reduces but cannot eliminate that ambiguity.","B01 is on the 20 m grid but retains native 60 m spatial information."],"created_utc":datetime.now(timezone.utc).isoformat(),"script":str(Path(__file__).resolve())}
    (OUT/f"{SCENE}_candidate_shallow_water_mask_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    rgb=np.moveaxis(stack[[3,2,1]]*np.pi,0,-1);shown=np.power(np.clip(rgb/.11,0,1),.85)
    fig,ax=plt.subplots(1,3,figsize=(17,6),constrained_layout=True);ax[0].imshow(shown);ax[0].contour(candidate,[.5],colors="red",linewidths=1);ax[0].set_title("Final water RGB\nred = candidate boundary");ax[1].imshow(mask,cmap="viridis",vmin=0,vmax=1);ax[1].set_title(f"Candidate shallow-water mask\n{candidate.sum():,} pixels ({candidate.sum()*400/1e6:.3f} km²)");im=ax[2].imshow(score,cmap="magma",vmin=0,vmax=np.nanpercentile(score[valid],99));ax[2].contour(candidate,[.5],colors="cyan",linewidths=.8);ax[2].set_title(f"Difference from deep-water spectrum\nthreshold = {bottom_threshold:.2f}");fig.colorbar(im,ax=ax[2],fraction=.046,label="Robust four-band distance");[a.axis("off") for a in ax[:2]];fig.suptitle(f"{SCENE} candidate shallow-water processing boundary",fontsize=18,weight="bold");fig.savefig(OUT/f"{SCENE}_candidate_shallow_water_mask_QC.png",dpi=180);plt.close(fig)
    print(json.dumps(metadata["counts"],indent=2));print(out_path)
if __name__=="__main__":main()
