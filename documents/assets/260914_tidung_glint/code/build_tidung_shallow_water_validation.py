#!/usr/bin/env python3
"""Build all-scene near-island shallow-water glint validation."""
from __future__ import annotations
import csv, json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt, uniform_filter
from scipy.stats import spearmanr

PROJECT=Path(r"C:\Users\phili\Documents\ChatGPT\ACOLITE-Glint Correction")
ROOT=Path(r"H:\Sentinel-2\Tidung\Tidung_Glint_Corrected_Products_20260913")
JOINT=PROJECT/"outputs"/"Tidung_Joint_HydroLight_Glint_Multiband_Experiment_20260911"
FULL=PROJECT/"outputs"/"Tidung_Full_Glint_All_Scenes_Experiment_20260911"
L2A=Path(r"H:\Sentinel-2\Tidung\L2A"); OUT=ROOT/"shallow-water-validation"
BANDS=("B02","B03","B04","B05","B06","B07","B08","B8A"); WAVE=np.array((492,560,665,704,740,783,833,865))
GROUPS=("LOW","MEDIUM","HIGH"); GCOL={"LOW":"#2563eb","MEDIUM":"#f59e0b","HIGH":"#dc2626"}
STCOL={"Original":"#334155","Cycle 0":"#0f766e","Final":"#2563eb"}

def read(path):
    with rasterio.open(path) as ds: return ds.read(1).astype(float),ds.profile

def retained_scenes():
    with (FULL/"all_33_scene_final_status.csv").open(encoding="utf-8-sig") as f:
        return [r["scene"] for r in csv.DictReader(f) if r["decision"].startswith("RETAIN_")]

def locate_scl(scene):
    p=list(L2A.glob(f"*{scene[:8]}*/GRANULE/*/IMG_DATA/R20m/*SCL_20m.jp2"))
    if not p: raise RuntimeError(f"No SCL raster for {scene}")
    return p[0]

def select_centres(mask,score,occupied,count=10):
    candidates=np.argwhere(mask); candidates=candidates[np.argsort(score[mask])[::-1]]; chosen=[]
    for y,x in candidates:
        if all((y-y0)**2+(x-x0)**2>=8**2 for y0,x0 in chosen+occupied):
            chosen.append((int(y),int(x)))
            if len(chosen)==count:return chosen
    raise RuntimeError(f"Only {len(chosen)} separated ROI centres")

def analyse_scene(scene):
    inp=JOINT/"02_Multiband_Inputs"/scene; cyc=JOINT/"03_Glint_ACOLITE_Cycle0"/scene
    fdir=ROOT/"FINAL_PRODUCTS"/scene/"01_Final_BOA_Reflectance"; original=[]; cycle0=[]; final=[]
    for b in BANDS:
        a,profile=read(inp/f"{b}_BOA_20m.tif"); original.append(a); cycle0.append(read(cyc/f"Cycle0_{b}.tif")[0]); final.append(read(fdir/f"{scene}_{b}_final_BOA_reflectance.tif")[0])
    original,cycle0,final=map(np.stack,(original,cycle0,final)); b11=read(inp/"B11_BOA_20m.tif")[0]; b12=read(inp/"B12_BOA_20m.tif")[0]
    scl=np.zeros((profile["height"],profile["width"]),np.uint8)
    with rasterio.open(locate_scl(scene)) as src:
        reproject(rasterio.band(src,1),scl,src_transform=src.transform,src_crs=src.crs,dst_transform=profile["transform"],dst_crs=profile["crs"],resampling=Resampling.nearest)
    water=scl==6; land=np.isin(scl,(4,5)); distance=distance_transform_edt(~land)
    complete=uniform_filter(water.astype(float),7,mode="constant")>.999
    finite=np.all(np.isfinite(original),axis=0)&np.all(np.isfinite(cycle0),axis=0)&np.all(np.isfinite(final),axis=0)
    shallow=water&complete&finite&(distance>=4)&(distance<=25)
    swir=uniform_filter(np.nan_to_num(np.minimum(b11,b12),nan=0),7,mode="nearest")
    q1,q2=np.nanquantile(swir[shallow],(1/3,2/3)); masks={"LOW":shallow&(swir<=q1),"MEDIUM":shallow&(swir>q1)&(swir<=q2),"HIGH":shallow&(swir>q2)}
    visible=np.nanmean(original[:3],axis=0); occupied=[]; centres=[]
    for g in GROUPS:
        picked=select_centres(masks[g],visible,occupied); occupied+=picked; centres += [(y,x,g) for y,x in picked]
    spectra={s:[] for s in STCOL}; records=[]
    for i,(y,x,g) in enumerate(centres,1):
        sl=np.s_[y-3:y+4,x-3:x+4]; vals=[np.nanmean(z[:,sl[0],sl[1]],axis=(1,2)) for z in (original,cycle0,final)]
        for key,val in zip(spectra,vals):spectra[key].append(val)
        records.append({"roi":f"SW{i:02d}","group":g,"row":y,"column":x,"distance_to_island_land_m":float(distance[y,x]*20),"raw_swir_indicator":float(np.nanmean(np.minimum(b11[sl],b12[sl]))),"cycle0_removed_visible_mean":float(np.mean(vals[0][:3]-vals[1][:3])),"final_additional_removed_visible_mean":float(np.mean(vals[1][:3]-vals[2][:3])),"final_minimum":float(np.min(vals[2]))})
    med={g:{stage:np.median(np.stack([values[i] for i,r in enumerate(records) if r["group"]==g]),axis=0) for stage,values in spectra.items()} for g in GROUPS}
    retained="Cycle 1" if not np.allclose(final,cycle0,equal_nan=True) else "Cycle 0"
    preservation_result=spearmanr(original[1][shallow],final[1][shallow],nan_policy="omit")
    preservation=float(getattr(preservation_result,"statistic",preservation_result.correlation))
    neg0=float(np.mean(np.stack(spectra["Cycle 0"])<0)*100); negf=float(np.mean(np.stack(spectra["Final"])<0)*100)
    roi_swir=np.array([r["raw_swir_indicator"] for r in records])
    stage_stats={}
    for stage,values in spectra.items():
        vis=np.array([float(np.mean(v[:3])) for v in values])
        by_group={g:float(np.median([vis[i] for i,r in enumerate(records) if r["group"]==g])) for g in GROUPS}
        corr,p=spearmanr(roi_swir,vis)
        stage_stats[stage]={"low":by_group["LOW"],"medium":by_group["MEDIUM"],"high":by_group["HIGH"],"highMinusLow":by_group["HIGH"]-by_group["LOW"],"spearman":float(corr),"p":float(p)}
    removal0=np.array([r["cycle0_removed_visible_mean"] for r in records]); removalf=np.array([r["final_additional_removed_visible_mean"] for r in records])
    removal_stats={}
    for name,values in (("Cycle 0",removal0),("After Cycle 0",removalf)):
        corr,p=spearmanr(roi_swir,values)
        removal_stats[name]={"low":float(np.median(values[:10])),"medium":float(np.median(values[10:20])),"high":float(np.median(values[20:30])),"spearman":float(corr),"p":float(p)}
    rgb=np.moveaxis(original[[2,1,0]],0,-1); lo,hi=np.nanpercentile(rgb,(2,98),axis=(0,1))
    map_name=f"{scene}_shallow_roi_locations.png"; fig,pa=plt.subplots(figsize=(13,7),constrained_layout=True)
    pa.imshow(np.clip((rgb-lo)/np.maximum(hi-lo,1e-6),0,1)); pa.contour(shallow,[.5],colors="#00ffff",linewidths=1.2)
    for i,(y,x,g) in enumerate(centres,1): pa.plot(x,y,"o",ms=9,color=GCOL[g],markeredgecolor="white"); pa.text(x+3,y,str(i),fontsize=8,color="white",weight="bold")
    for g in GROUPS: pa.plot([],[],"o",ms=9,color=GCOL[g],label=f"{g}: 10 ROIs")
    pa.set_title("Near-island shallow-water zone and 30 ROI locations",fontsize=18); pa.set_xlabel("Image column (20 m pixel)"); pa.set_ylabel("Image row (20 m pixel)"); pa.legend()
    fig.savefig(OUT/map_name,dpi=160); plt.close(fig)
    rank_name=f"{scene}_shallow_glint_ranking.png"; fig,pa=plt.subplots(figsize=(13,5),constrained_layout=True)
    ordered=sorted(records,key=lambda r:r["raw_swir_indicator"])
    for i,r in enumerate(ordered): pa.scatter(i+1,r["raw_swir_indicator"],s=70,color=GCOL[r["group"]]); pa.text(i+1,r["raw_swir_indicator"],r["roi"],fontsize=7,rotation=55,ha="left",va="bottom")
    pa.axhline(q1,color="#64748b",ls="--",label=f"LOW limit {q1:.6f}"); pa.axhline(q2,color="#111827",ls="--",label=f"HIGH limit {q2:.6f}")
    pa.set_title("Thirty shallow-water ROIs ranked by SWIR glint indicator",fontsize=18); pa.set_xlabel("ROI rank from lower to higher glint estimate"); pa.set_ylabel("SWIR glint indicator"); pa.grid(alpha=.2); pa.legend()
    fig.savefig(OUT/rank_name,dpi=160); plt.close(fig)
    spectra_name=f"{scene}_shallow_spectral_steps.png"; fig,axes=plt.subplots(3,1,figsize=(13,15),constrained_layout=True)
    for pa,g in zip(axes,GROUPS):
        ids=[i for i,r in enumerate(records) if r["group"]==g]
        for stage in spectra:
            for i in ids:pa.plot(WAVE,spectra[stage][i],color=STCOL[stage],alpha=.10,lw=1)
            pa.plot(WAVE,med[g][stage],color=STCOL[stage],lw=3,label=(f"Final ({retained} retained)" if stage=="Final" else stage))
        pa.set_title(f"{g}: 10 shallow-water ROIs"); pa.set_xlabel("Wavelength (nm)"); pa.set_ylabel("BOA reflectance"); pa.legend()
        pa.grid(alpha=.2)
    fig.savefig(OUT/spectra_name,dpi=160); plt.close(fig)
    csv_name=f"{scene}_shallow_rois.csv"
    with (OUT/csv_name).open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
    return {"scene":scene,"retained":retained,"mapFigure":map_name,"rankFigure":rank_name,"spectraFigure":spectra_name,"csv":csv_name,"q1":float(q1),"q2":float(q2),"negative0":neg0,"negativeFinal":negf,"preservation":preservation,"stageStats":stage_stats,"removalStats":removal_stats,"records":records,"spectra":{stage:[[float(x) for x in v] for v in values] for stage,values in spectra.items()},"medians":{g:{s:[float(x) for x in v] for s,v in m.items()} for g,m in med.items()}}

def build_html(results):
    data=json.dumps({"bands":BANDS,"wave":WAVE.tolist(),"scenes":results},separators=(",",":"))
    html='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Shallow-water glint validation</title><style>
body{font:16px Arial;color:#142033;margin:0;background:#f6f8fb}main{max-width:1250px;margin:auto;padding:16px}.card{background:#fff;border:1px solid #b7c4d4;border-radius:8px;padding:20px;margin:16px 0}h1,h2{margin-top:0}select,button{font-size:16px;padding:8px}img{display:block;width:100%;height:auto;border:1px solid #94a3b8}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}.metrics div{padding:12px;border:1px solid #cbd5e1}.metrics b{display:block;font-size:1.2rem}table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:7px;text-align:left}th{background:#eef3f8}.note{border-left:5px solid #0f766e;background:#eafafa;padding:12px}.warn{border-left:5px solid #b45309;background:#fff7ed;padding:12px}.stage-chart{display:block;width:100%;height:auto;border:1px solid #94a3b8;margin:12px 0 20px}.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0}.legend{display:flex;gap:20px;flex-wrap:wrap}.line-key{display:inline-block;width:28px;height:4px;margin-right:6px;vertical-align:middle}</style></head><body><main>
<div class="card"><h1>Shallow-water glint validation</h1><label><b>Scene: </b><select id="scene"></select></label><p>Each retained date is checked in the same order below. HydroLight is not used in this tab.</p></div><div id="content"></div>
<script>const D=__DATA__,sel=document.getElementById('scene');D.scenes.forEach((s,i)=>sel.add(new Option(s.scene+' · '+s.retained,i)));
const groupColors={LOW:'#2563eb',MEDIUM:'#f59e0b',HIGH:'#dc2626'};
function shallowStageChart(s,stage,showAll){const W=1160,H=410,p={l:82,r:24,t:54,b:58},all=Object.values(s.spectra).flat(2).filter(Number.isFinite),y0=Math.min(0,Math.min(...all)),y1=Math.max(...all)*1.05,X=i=>p.l+i/(D.wave.length-1)*(W-p.l-p.r),Y=v=>H-p.b-(v-y0)/(y1-y0)*(H-p.t-p.b);let z=`<rect width="${W}" height="${H}" fill="white"/><text x="${W/2}" y="30" text-anchor="middle" font-size="23" font-weight="700">${stage==='Final'?(s.retained+' — final retained'):stage}</text>`;for(let j=0;j<5;j++){const v=y0+(y1-y0)*j/4,y=Y(v);z+=`<line x1="${p.l}" x2="${W-p.r}" y1="${y}" y2="${y}" stroke="#dbe3ea"/><text x="${p.l-10}" y="${y+5}" text-anchor="end" font-size="14">${v.toFixed(3)}</text>`}D.wave.forEach((w,i)=>z+=`<text x="${X(i)}" y="${H-27}" text-anchor="middle" font-size="14">${w}</text>`);if(showAll)for(let i=0;i<s.records.length;i++){const g=s.records[i].group,pts=s.spectra[stage][i].map((v,j)=>`${X(j)},${Y(v)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${groupColors[g]}" stroke-opacity=".18" stroke-width="1.5"/>`}for(const g of ['LOW','MEDIUM','HIGH']){const pts=s.medians[g][stage].map((v,j)=>`${X(j)},${Y(v)}`).join(' ');z+=`<polyline points="${pts}" fill="none" stroke="${groupColors[g]}" stroke-width="5"/>`}z+=`<text x="${W/2}" y="${H-5}" text-anchor="middle" font-size="17">Wavelength (nm)</text><text transform="translate(22 ${H/2}) rotate(-90)" text-anchor="middle" font-size="17">BOA reflectance</text>`;return `<svg class="stage-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${stage} shallow-water spectra">${z}</svg>`}
function renderStageCharts(s){const showAll=document.getElementById('shallowGraphMode').value==='all';document.getElementById('shallowStageCharts').innerHTML=['Original','Cycle 0','Final'].map(k=>shallowStageChart(s,k,showAll)).join('')}
function render(){const s=D.scenes[+sel.value||0],med=[];for(const g of ['LOW','MEDIUM','HIGH'])for(let i=0;i<D.bands.length;i++)med.push(`<tr><td>${g}</td><td>${D.bands[i]} (${D.wave[i]} nm)</td><td>${s.medians[g]['Original'][i].toFixed(6)}</td><td>${s.medians[g]['Cycle 0'][i].toFixed(6)}</td><td>${s.medians[g]['Final'][i].toFixed(6)}</td></tr>`);const rois=s.records.map(r=>`<tr><td>${r.roi}</td><td>${r.group}</td><td>${r.distance_to_island_land_m.toFixed(0)}</td><td>${r.raw_swir_indicator.toFixed(6)}</td><td>${r.cycle0_removed_visible_mean.toFixed(6)}</td><td>${r.final_additional_removed_visible_mean.toFixed(6)}</td></tr>`).join('');document.getElementById('content').innerHTML=`
<div class="card"><h2>1. Shallow-water area</h2><p>Valid water located 80–500 m from the mapped island land is used as the shallow-water zone. This distance-based definition is used because measured bathymetry is unavailable.</p><img src="${s.mapFigure}" alt="Shallow-water zone and ROI locations"><p class="note"><b>Read the map:</b> cyan outlines the selected near-island water. Blue points are LOW, orange points are MEDIUM and red points are HIGH. The numbered points are the exact 30 ROI locations.</p><p><b>Conclusion:</b> only water around the island inside the cyan zone is evaluated below.</p></div>
<div class="card"><h2>2. Shallow-water ROI glint classification</h2><p>Each point is the real 7×7-pixel mean SWIR glint indicator for one shallow-water ROI. The 30 values are ranked separately for this date.</p><img src="${s.rankFigure}" alt="Thirty shallow-water ROIs ranked by glint"><div class="metrics"><div><b>LOW</b>≤ ${s.q1.toFixed(6)}</div><div><b>MEDIUM</b>&gt; ${s.q1.toFixed(6)} to ≤ ${s.q2.toFixed(6)}</div><div><b>HIGH</b>&gt; ${s.q2.toFixed(6)}</div></div><p class="note"><b>Read the graph:</b> points farther upward have a larger estimated surface-reflection signal. The dashed lines divide this date into 10 LOW, 10 MEDIUM and 10 HIGH ROIs.</p></div>
<div class="card"><h2>3. Shallow-water spectra before and after correction</h2><p>These three graphs show the same 30 shallow-water ROIs at the same wavelengths. All graphs use one fixed vertical scale, so the change in height is directly comparable.</p><div class="controls"><label><b>Graph view:</b> <select id="shallowGraphMode"><option value="median">LOW, MEDIUM and HIGH medians</option><option value="all">All 30 ROI spectra and medians</option></select></label><span class="legend"><span><i class="line-key" style="background:#2563eb"></i>LOW</span><span><i class="line-key" style="background:#f59e0b"></i>MEDIUM</span><span><i class="line-key" style="background:#dc2626"></i>HIGH</span></span></div><div id="shallowStageCharts"></div><table><tr><th>Stage</th><th>LOW visible median</th><th>MEDIUM visible median</th><th>HIGH visible median</th><th>HIGH − LOW</th></tr>${['Original','Cycle 0','Final'].map(k=>`<tr><td>${k==='Final'?s.retained+' final':k}</td><td>${s.stageStats[k].low.toFixed(6)}</td><td>${s.stageStats[k].medium.toFixed(6)}</td><td>${s.stageStats[k].high.toFixed(6)}</td><td>${s.stageStats[k].highMinusLow.toFixed(6)}</td></tr>`).join('')}</table><p class="note"><b>Interpretation:</b> compare each colored curve vertically from Original to Cycle 0 to Final. A lower curve means reflectance was removed. A smaller HIGH − LOW value means the original glint-ranked groups became less separated. However, shallow-water bottom type and depth can also produce real separation, so convergence is supporting evidence rather than proof that all glint was removed.</p><table><tr><th>Cycle 0 removal check</th><th>LOW</th><th>MEDIUM</th><th>HIGH</th></tr><tr><td>Median visible reflectance removed</td><td>${s.removalStats['Cycle 0'].low.toFixed(6)}</td><td>${s.removalStats['Cycle 0'].medium.toFixed(6)}</td><td>${s.removalStats['Cycle 0'].high.toFixed(6)}</td></tr></table><p><b>Conclusion:</b> Cycle 0 applied the first glint-related reduction. ${s.retained==='Cycle 1'?'The third graph shows the additional accepted Cycle 1 change.':'Cycle 1 was not authorized, so the Cycle 0 and Final graphs are intentionally identical.'}</p></div>
<div class="card"><h2>4. Residual pattern after Cycle 0</h2><table><tr><th>Check after Cycle 0</th><th>Value</th><th>Meaning</th></tr><tr><td>LOW median visible reflectance</td><td>${s.stageStats['Cycle 0'].low.toFixed(6)}</td><td>Corrected brightness in the original LOW group</td></tr><tr><td>HIGH median visible reflectance</td><td>${s.stageStats['Cycle 0'].high.toFixed(6)}</td><td>Corrected brightness in the original HIGH group</td></tr><tr><td>HIGH minus LOW</td><td>${s.stageStats['Cycle 0'].highMinusLow.toFixed(6)}</td><td>Remaining group separation</td></tr><tr><td>Relation with original SWIR ranking</td><td>r = ${s.stageStats['Cycle 0'].spearman.toFixed(3)}; p = ${s.stageStats['Cycle 0'].p.toFixed(6)}</td><td>Whether corrected shallow-water brightness still follows the original glint ranking</td></tr></table><p class="warn"><b>Interpretation:</b> these are shallow-water residual-pattern checks, not a stand-alone proof of residual glint. Bottom type and water depth can also make HIGH and LOW groups different. HydroLight is deliberately not used here.</p></div>
<div class="card"><h2>5. Cycle 1 decision</h2><p><b>Full-scene retained decision:</b> ${s.retained}.</p><p>${s.retained==='Cycle 1'?'The complete deep-water scene detector authorized Cycle 1. This tab therefore checks how that accepted correction behaved in shallow water.':'The complete deep-water detector did not authorize an additional correction. Cycle 0 therefore remains the final product, including in this shallow-water validation.'}</p><table><tr><th>Additional median visible removal</th><th>LOW</th><th>MEDIUM</th><th>HIGH</th></tr><tr><td>Cycle 0 to final</td><td>${s.removalStats['After Cycle 0'].low.toFixed(6)}</td><td>${s.removalStats['After Cycle 0'].medium.toFixed(6)}</td><td>${s.removalStats['After Cycle 0'].high.toFixed(6)}</td></tr></table></div>
<div class="card"><h2>6. Final repeated shallow-water check</h2><table><tr><th>Stage</th><th>LOW visible median</th><th>MEDIUM visible median</th><th>HIGH visible median</th><th>HIGH minus LOW</th><th>Relation with original SWIR ranking</th></tr>${['Original','Cycle 0','Final'].map(k=>`<tr><td>${k==='Final'?s.retained+' final':k}</td><td>${s.stageStats[k].low.toFixed(6)}</td><td>${s.stageStats[k].medium.toFixed(6)}</td><td>${s.stageStats[k].high.toFixed(6)}</td><td>${s.stageStats[k].highMinusLow.toFixed(6)}</td><td>r ${s.stageStats[k].spearman.toFixed(3)}; p ${s.stageStats[k].p.toFixed(6)}</td></tr>`).join('')}</table><div class="metrics"><div><b>${s.negative0.toFixed(3)}%</b>negative values after Cycle 0</div><div><b>${s.negativeFinal.toFixed(3)}%</b>negative values in final ROIs</div><div><b>${s.preservation.toFixed(3)}</b>B03 spatial rank preserved</div><div><b>${s.retained}</b>final retained result</div></div><p class="note"><b>Final conclusion:</b> ${s.negativeFinal<=1?'the final shallow-water ROI spectra pass the negative-value safety check.':'negative values exceed 1%; this scene requires review.'} The spatial value tests preservation of relative shallow features. It does not validate measured water depth or prove that physical glint equals exactly zero.</p><details><summary><b>Show exact group-median spectra</b></summary><table><tr><th>Group</th><th>Band</th><th>Original</th><th>Cycle 0</th><th>Final</th></tr>${med.join('')}</table></details></div>
<div class="card"><h2>7. ROI numerical results</h2><details><summary><b>Show all 30 ROI values</b></summary><table><tr><th>ROI</th><th>Group</th><th>Distance to land (m)</th><th>SWIR indicator</th><th>Removed by Cycle 0</th><th>Removed after Cycle 0</th></tr>${rois}</table></details><p><a href="${s.csv}" download>Download this scene's ROI values (CSV)</a></p></div>`;document.getElementById('shallowGraphMode').onchange=()=>renderStageCharts(s);renderStageCharts(s)}sel.onchange=render;render();</script></main></body></html>'''.replace('__DATA__',data)
    html=html.replace(
        'Each point is the real 7×7-pixel mean SWIR glint indicator for one shallow-water ROI. The 30 values are ranked separately for this date.',
        '<b>How the ranges are chosen:</b> all eligible 7×7 near-island water centres are ranked using their mean SWIR glint indicator. The 33⅓ percentile is the LOW/MEDIUM boundary and the 66⅔ percentile is the MEDIUM/HIGH boundary. Ten spatially separated ROIs are then selected from each pool.<div style="font-weight:700;text-align:center;padding:14px;margin:12px 0;border:2px solid #2563eb;background:#eff6ff">Eligible shallow-water centres → calculate mean glint indicator → sort → divide at 33⅓% and 66⅔% → select 10 LOW + 10 MEDIUM + 10 HIGH</div>'
    )
    (OUT/"index.html").write_text(html,encoding="utf-8"); (OUT/"all_shallow_water_metrics.json").write_text(json.dumps(results,indent=2),encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True); results=[]
    for scene in retained_scenes(): print(f"Analysing {scene}",flush=True); results.append(analyse_scene(scene))
    build_html(results); print(f"Built {len(results)} retained scenes")
if __name__=="__main__":main()
