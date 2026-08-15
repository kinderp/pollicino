import tempfile, unittest, torch
from main import ModelConfig, ByteTransformer, save_checkpoint, load_checkpoint, select_best_epoch
class TestValidationPublic(unittest.TestCase):
    def test_best_epoch(self): self.assertEqual(select_best_epoch([3.0,2.0,2.5]),1)
    def test_checkpoint_roundtrip(self):
        cfg=ModelConfig(context_length=4,d_model=8,n_heads=2,n_layers=1,d_ff=16); m=ByteTransformer(cfg); opt=torch.optim.AdamW(m.parameters(),lr=1e-3)
        before={k:v.clone() for k,v in m.state_dict().items()}
        with tempfile.NamedTemporaryFile(suffix='.pt') as f:
            save_checkpoint(f.name,m,opt,7,cfg,{'val_bpb':4.2});
            with torch.no_grad(): next(m.parameters()).add_(1.0)
            meta=load_checkpoint(f.name,m,opt)
        self.assertEqual(meta['step'],7); self.assertEqual(meta['metrics']['val_bpb'],4.2)
        for k,v in m.state_dict().items(): self.assertTrue(torch.equal(v,before[k]))
if __name__=='__main__': unittest.main()
