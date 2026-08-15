from __future__ import annotations
import json,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
CONFIGS={'base-c64':dict(context=64,d_model=32,heads=4,layers=2,d_ff=64),'medium-c32':dict(context=32,d_model=48,heads=4,layers=2,d_ff=96),'medium-c64':dict(context=64,d_model=48,heads=4,layers=2,d_ff=96)}
SEEDS=(1337,2026,4242)

def main():
 rows=[]; outdir=HERE/'confirm-runs'; outdir.mkdir(exist_ok=True)
 for name,c in CONFIGS.items():
  for seed in SEEDS:
   batch=1024//c['context']; evalw=max(8,4096//c['context']); out=outdir/f'{name}-s{seed}.json'
   cmd=[sys.executable,str(HERE/'run_one.py'),'--name',name,'--context',str(c['context']),'--d-model',str(c['d_model']),'--heads',str(c['heads']),'--layers',str(c['layers']),'--d-ff',str(c['d_ff']),'--steps','200','--batch-size',str(batch),'--lr','0.003','--seed',str(seed),'--eval-windows',str(evalw),'--output',str(out)]
   subprocess.run(cmd,check=True); rows.append(json.loads(out.read_text()))
 summary=[]
 for name in CONFIGS:
  rs=[r for r in rows if r['name']==name]; summary.append({'name':name,'mean_test_bpb':statistics.mean(r['test_bpb'] for r in rs),'stdev_test_bpb':statistics.stdev(r['test_bpb'] for r in rs),'mean_validation_bpb':statistics.mean(r['final_validation_bpb'] for r in rs)})
 (HERE/'confirmation-local.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2)+'\n')
if __name__=='__main__': main()
