#!/usr/bin/env python3
"""Small desktop interface for the Tidung glint pipeline."""
from __future__ import annotations
import json
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tidung glint processing")
        self.geometry("900x650")
        self.config_path = tk.StringVar(value=str(ROOT / "config.json"))
        self.mode = tk.StringVar(value="one-scene")
        self.scene = tk.StringVar(value="20240925_S2A")
        self._row("Configuration JSON", self.config_path, self.choose_config, 0)
        ttk.Label(self, text="Processing mode").grid(row=1, column=0, sticky="w", padx=12, pady=8)
        ttk.Combobox(self, textvariable=self.mode, state="readonly", values=("one-scene", "all-scenes", "export"), width=28).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Label(self, text="Scene (one-scene mode)").grid(row=2, column=0, sticky="w", padx=12, pady=8)
        ttk.Entry(self, textvariable=self.scene).grid(row=2, column=1, sticky="ew", padx=8)
        buttons=ttk.Frame(self); buttons.grid(row=3,column=0,columnspan=3,sticky="ew",padx=12,pady=10)
        ttk.Button(buttons,text="1. Validate setup",command=lambda:self.run("validate")).pack(side="left",padx=4)
        ttk.Button(buttons,text="2. Run processing",command=lambda:self.run("process")).pack(side="left",padx=4)
        ttk.Button(buttons,text="Open output folder",command=self.open_output).pack(side="left",padx=4)
        ttk.Button(buttons,text="Open HTML report",command=self.open_report).pack(side="left",padx=4)
        ttk.Label(self,text="Progress and messages").grid(row=4,column=0,columnspan=3,sticky="w",padx=12)
        self.log=tk.Text(self,height=22,wrap="word"); self.log.grid(row=5,column=0,columnspan=3,sticky="nsew",padx=12,pady=6)
        ttk.Label(self,text="Expected outputs: final BOA GeoTIFFs; Rrs and rrs GeoTIFFs; per-pixel tables; ROI spectra; QC/decision files; figures; HTML report and processing log.",wraplength=850).grid(row=6,column=0,columnspan=3,sticky="w",padx=12,pady=8)
        self.columnconfigure(1,weight=1); self.rowconfigure(5,weight=1)
    def _row(self,label,var,command,row):
        ttk.Label(self,text=label).grid(row=row,column=0,sticky="w",padx=12,pady=8)
        ttk.Entry(self,textvariable=var).grid(row=row,column=1,sticky="ew",padx=8)
        ttk.Button(self,text="Browse",command=command).grid(row=row,column=2,padx=12)
    def choose_config(self):
        value=filedialog.askopenfilename(initialdir=ROOT,filetypes=(("JSON","*.json"),("All files","*.*")))
        if value:self.config_path.set(value)
    def cfg(self):
        return json.loads(Path(self.config_path.get()).read_text(encoding="utf-8"))
    def run(self,kind):
        config=self.config_path.get()
        if not Path(config).exists(): messagebox.showerror("Missing configuration",config); return
        if kind=="validate": cmd=[sys.executable,str(ROOT/"validate_setup.py"),config]
        else:
            cmd=[sys.executable,str(ROOT/"run_pipeline.py"),"--config",config,"--mode",self.mode.get()]
            if self.mode.get()=="one-scene":cmd += ["--scene",self.scene.get().strip()]
        self.log.insert("end","\n> "+subprocess.list2cmdline(cmd)+"\n"); self.log.see("end")
        threading.Thread(target=self._worker,args=(cmd,),daemon=True).start()
    def _worker(self,cmd):
        process=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in process.stdout:self.after(0,self._append,line)
        code=process.wait(); self.after(0,self._append,f"\nFinished with exit code {code}.\n")
    def _append(self,text): self.log.insert("end",text); self.log.see("end")
    def output(self): return Path(self.cfg()["final_product_output"]).expanduser()
    def open_output(self):
        p=self.output(); p.mkdir(parents=True,exist_ok=True); subprocess.Popen(["explorer",str(p)])
    def open_report(self):
        p=self.output()/"Tidung_Glint_Correction_Results.html"
        if not p.exists(): messagebox.showinfo("Report not found",f"Expected report:\n{p}"); return
        webbrowser.open(p.as_uri())

if __name__ == "__main__": App().mainloop()
