from __future__ import annotations
import zlib
# Baseline funzionante: puoi sostituirla con il tuo codec POLLICINO.
def compress(data:bytes)->bytes: return zlib.compress(data,level=9)
def decompress(blob:bytes)->bytes: return zlib.decompress(blob)
