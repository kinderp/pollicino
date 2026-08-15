from __future__ import annotations
import math, random

VOCAB_SIZE=256


def softmax(logits: list[float]) -> list[float]:
    m=max(logits); e=[math.exp(x-m) for x in logits]; s=sum(e); return [x/s for x in e]


def make_examples(data: bytes, context_size: int=2) -> list[tuple[list[int],int]]:
    if context_size <= 0: raise ValueError("context_size must be positive")
    return [(list(data[i-context_size:i]), data[i]) for i in range(context_size,len(data))]


def init_model(context_size: int=2, embedding_dim: int=4, hidden_dim: int=8, seed: int=0, scale: float=0.08) -> dict:
    if min(context_size,embedding_dim,hidden_dim) <= 0: raise ValueError("dimensions must be positive")
    rng=random.Random(seed)
    def matrix(rows,cols): return [[rng.uniform(-scale,scale) for _ in range(cols)] for _ in range(rows)]
    input_dim=context_size*embedding_dim
    return {
        'context_size':context_size,'embedding_dim':embedding_dim,'hidden_dim':hidden_dim,
        'embedding':matrix(VOCAB_SIZE,embedding_dim),
        'w1':matrix(hidden_dim,input_dim),'b1':[0.0]*hidden_dim,
        'w2':matrix(VOCAB_SIZE,hidden_dim),'b2':[0.0]*VOCAB_SIZE,
    }


def forward(model: dict, context: list[int]) -> tuple[list[float],dict]:
    if len(context) != model['context_size']: raise ValueError("wrong context length")
    x=[]
    for token in context:
        if not 0 <= token < VOCAB_SIZE: raise IndexError("byte outside vocabulary")
        x.extend(model['embedding'][token])
    z1=[sum(w*v for w,v in zip(row,x))+b for row,b in zip(model['w1'],model['b1'])]
    h=[math.tanh(z) for z in z1]
    logits=[sum(w*v for w,v in zip(row,h))+b for row,b in zip(model['w2'],model['b2'])]
    probs=softmax(logits)
    return probs, {'x':x,'h':h,'context':context}


def loss_bits(model: dict, examples: list[tuple[list[int],int]]) -> float:
    if not examples: return 0.0
    total=0.0
    for context,target in examples:
        p,_=forward(model,context)
        total += -math.log2(max(p[target],1e-300))
    return total/len(examples)


def train_step(model: dict, context: list[int], target: int, learning_rate: float=0.05) -> float:
    if learning_rate <= 0: raise ValueError("learning_rate must be positive")
    probs,cache=forward(model,context)
    h=cache['h']; x=cache['x']
    loss=-math.log(max(probs[target],1e-300))
    dlogits=probs.copy(); dlogits[target]-=1.0
    old_w2=[row.copy() for row in model['w2']]
    for out in range(VOCAB_SIZE):
        g=dlogits[out]
        for j in range(model['hidden_dim']): model['w2'][out][j] -= learning_rate*g*h[j]
        model['b2'][out] -= learning_rate*g
    dh=[sum(old_w2[out][j]*dlogits[out] for out in range(VOCAB_SIZE)) for j in range(model['hidden_dim'])]
    dz=[dh[j]*(1.0-h[j]*h[j]) for j in range(model['hidden_dim'])]
    old_w1=[row.copy() for row in model['w1']]
    for j in range(model['hidden_dim']):
        for k in range(len(x)): model['w1'][j][k] -= learning_rate*dz[j]*x[k]
        model['b1'][j] -= learning_rate*dz[j]
    dx=[sum(old_w1[j][k]*dz[j] for j in range(model['hidden_dim'])) for k in range(len(x))]
    d=model['embedding_dim']
    for pos,token in enumerate(context):
        for j in range(d): model['embedding'][token][j] -= learning_rate*dx[pos*d+j]
    return loss


def train(model: dict, data: bytes, epochs: int=5, learning_rate: float=0.05) -> list[float]:
    examples=make_examples(data,model['context_size'])
    history=[]
    for _ in range(epochs):
        for context,target in examples: train_step(model,context,target,learning_rate)
        history.append(loss_bits(model,examples))
    return history


def uniform_bpb() -> float: return 8.0


def bigram_bpb(train_data: bytes, test_data: bytes, alpha: float=1.0) -> float:
    if alpha <= 0: raise ValueError("alpha must be positive")
    counts=[[0]*VOCAB_SIZE for _ in range(VOCAB_SIZE)]
    totals=[0]*VOCAB_SIZE
    for a,b in zip(train_data,train_data[1:]): counts[a][b]+=1; totals[a]+=1
    if len(test_data)<2: return 0.0
    bits=0.0
    for a,b in zip(test_data,test_data[1:]):
        p=(counts[a][b]+alpha)/(totals[a]+alpha*VOCAB_SIZE)
        bits += -math.log2(p)
    return bits/(len(test_data)-1)
