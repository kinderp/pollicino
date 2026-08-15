from __future__ import annotations
import zlib
def compress(data): return zlib.compress(data,level=9)
def decompress(blob): return zlib.decompress(blob)
