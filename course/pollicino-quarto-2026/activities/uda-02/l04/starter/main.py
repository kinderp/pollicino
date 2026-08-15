from __future__ import annotations
from dataclasses import dataclass
import math
from pathlib import Path
VOCAB_SIZE=256
@dataclass
class NGramModel:
 order:int; context_counts:dict[bytes,list[int]]; global_counts:list[int]

def train_ngram(data:bytes,order:int=1)->NGramModel:
 # TODO: conta i target condizionati dagli ultimi `order` byte e conserva i conteggi globali.
 raise NotImplementedError

def context_distribution(model:NGramModel,context:bytes,alpha:float=0.5)->list[float]:
 # TODO: usa il contesto se visto, altrimenti i conteggi globali; applica add-alpha smoothing.
 raise NotImplementedError

def next_byte_probability(model,context,target,alpha=0.5): return context_distribution(model,context,alpha)[target]

def evaluate_bpb(model:NGramModel,data:bytes,alpha:float=0.5)->float:
 # TODO: valuta senza aggiornare il modello; media di -log2(p) sul byte corretto.
 raise NotImplementedError

def most_likely_next(model,context,alpha=0.5):
 # TODO: restituisci byte e probabilita massimi.
 raise NotImplementedError

def compare_orders(train,test,max_order=3,alpha=0.5): return [(o,evaluate_bpb(train_ngram(train,o),test,alpha)) for o in range(max_order+1)]
if __name__=="__main__":
 train=Path("fixtures/train.txt").read_bytes(); test=Path("fixtures/test.txt").read_bytes()
 for o,bpb in compare_orders(train,test): print(f"order={o} test_bpb={bpb:.4f}")
