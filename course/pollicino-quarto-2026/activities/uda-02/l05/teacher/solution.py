from __future__ import annotations
from pathlib import Path
from reference_ngram import evaluate_ngram_bpb

def split_train_test(data,train_fraction=0.8):
 if not 0<train_fraction<1: raise ValueError("train_fraction must be between 0 and 1")
 cut=int(len(data)*train_fraction)
 if len(data)>=2: cut=min(max(cut,1),len(data)-1)
 return data[:cut],data[cut:]

def uniform_bpb(): return 8.0

def ideal_ratio_from_bpb(bpb):
 if bpb<0: raise ValueError("bpb must be non-negative")
 return bpb/8.0

def benchmark_models(train,test,max_order=3,alpha=0.5):
 results=[{"model":"uniform","order":-1,"bpb":8.0,"ideal_ratio":1.0}]
 for order in range(max_order+1):
  bpb=evaluate_ngram_bpb(train,test,order,alpha); results.append({"model":f"{order}-gram","order":order,"bpb":bpb,"ideal_ratio":ideal_ratio_from_bpb(bpb)})
 return results

def format_table(results):
 lines=["model\tbpb\tideal_ratio"]
 for row in results: lines.append(f"{row['model']}\t{float(row['bpb']):.4f}\t{float(row['ideal_ratio']):.4f}")
 return "\n".join(lines)
if __name__=="__main__":
 data=Path("fixtures/corpus.txt").read_bytes(); train,test=split_train_test(data,0.8); print(f"train_bytes={len(train)} test_bytes={len(test)}"); print(format_table(benchmark_models(train,test)))
