from __future__ import annotations
import math
from fractions import Fraction
def normalized_intervals(weights):
    if not weights or any((not isinstance(v,int)) or v<=0 for v in weights.values()): raise ValueError('weights must be positive integers')
    total=sum(weights.values()); running=0; out={}
    for symbol,weight in weights.items(): out[symbol]=(Fraction(running,total),Fraction(running+weight,total)); running+=weight
    return out
def arithmetic_trace(sequence,weights):
    intervals=normalized_intervals(weights); low=Fraction(0); high=Fraction(1); trace=[]
    for symbol in sequence:
        if symbol not in intervals: raise ValueError(f'unknown symbol: {symbol}')
        a,b=intervals[symbol]; width=high-low; old_low=low; low=old_low+width*a; high=old_low+width*b; trace.append((low,high))
    return trace
def interval_information_bits(low,high):
    width=high-low
    if width<=0: raise ValueError('interval must have positive width')
    return -math.log2(float(width))
