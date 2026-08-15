from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SIZES={'tiny':dict(d_model=16,heads=2,layers=1,d_ff=32),'base':dict(d_model=32,heads=4,layers=2,d_ff=64),'medium':dict(d_model=48,heads=4,layers=2,d_ff=96)}
TOKENS_PER_STEP=1024

def run(size,context,steps):
 p=SIZES[size]; batch=max(1,TOKENS_PER_STEP//context); evalw=max(4,2048//context); name=f'{size}-c{context}' + ('-budget' if context==256 else '')
 out=HERE/'runs'/f'{name}.json'; out.parent.mkdir(exist_ok=True)
 cmd=[sys.executable,str(HERE/'run_one.py'),'--name',name,'--context',str(context),'--d-model',str(p['d_model']),'--heads',str(p['heads']),'--layers',str(p['layers']),'--d-ff',str(p['d_ff']),'--steps',str(steps),'--batch-size',str(batch),'--lr','0.003','--seed','1337','--eval-windows',str(evalw),'--output',str(out)]
 subprocess.run(cmd,check=True); return json.loads(out.read_text())

def main():
 rows=[]
 for size in SIZES:
  for context in (32,64,128): rows.append(run(size,context,80))
  rows.append(run(size,256,20))
 (HERE/'sweep-local.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__': main()
