from __future__ import annotations
import ast
from pathlib import Path
import pytest
from pollicino.model_spec import ModelSpec, expected_parameter_count

def test_reference_spec_parameter_count(): assert expected_parameter_count(ModelSpec()) == 34_816

def test_invalid_head_partition_is_rejected():
    with pytest.raises(ValueError): ModelSpec(d_model=30,n_heads=4)

def test_pytorch_backend_matches_spec_and_is_causal():
    torch=pytest.importorskip('torch'); from pollicino.backends.pytorch.model import ByteTransformer,parameter_count
    spec=ModelSpec(context_length=8,d_model=16,n_heads=4,n_layers=1,d_ff=32); torch.manual_seed(7); model=ByteTransformer(spec).eval()
    assert parameter_count(ByteTransformer(ModelSpec()))==expected_parameter_count(ModelSpec())
    a=torch.tensor([[1,2,3,4,5,6]],dtype=torch.long); b=torch.tensor([[1,2,3,99,100,101]],dtype=torch.long)
    with torch.no_grad(): la,lb=model(a),model(b)
    assert la.shape==(1,6,256); assert torch.allclose(la[:,:3],lb[:,:3],atol=1e-6)

def test_mlx_backend_source_tracks_reference_contract():
    source=(Path(__file__).resolve().parents[1]/'src/pollicino/backends/mlx/model.py').read_text(encoding='utf-8'); ast.parse(source)
    for token in ('mx.softmax','mx.swapaxes','nn.LayerNorm','nn.losses.cross_entropy'): assert token in source
