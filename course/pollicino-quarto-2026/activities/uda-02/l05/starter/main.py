from __future__ import annotations
from pathlib import Path
from reference_ngram import evaluate_ngram_bpb

def split_train_test(data:bytes,train_fraction:float=0.8)->tuple[bytes,bytes]:
 # TODO: crea due parti contigue e non sovrapposte; il test non va usato per il training.
 raise NotImplementedError

def uniform_bpb()->float:
 # TODO: costo di un alfabeto uniforme di 256 byte.
 raise NotImplementedError

def ideal_ratio_from_bpb(bpb:float)->float:
 # TODO: rapporto ideale rispetto agli 8 bit raw per byte.
 raise NotImplementedError

def benchmark_models(train:bytes,test:bytes,max_order:int=3,alpha:float=0.5):
 # TODO: valuta uniform e n-gram 0..max_order sulla stessa porzione di test.
 raise NotImplementedError

def format_table(results):
 lines=["model\tbpb\tideal_ratio"]
 for row in results: lines.append(f"{row['model']}\t{float(row['bpb']):.4f}\t{float(row['ideal_ratio']):.4f}")
 return "\n".join(lines)
if __name__=="__main__":
 data=Path("fixtures/corpus.txt").read_bytes(); train,test=split_train_test(data,0.8); print(f"train_bytes={len(train)} test_bytes={len(test)}"); print(format_table(benchmark_models(train,test)))
