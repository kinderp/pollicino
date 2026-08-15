import unittest
from main import result_record, validate_record, compare_records
class TestBenchmarkPublic(unittest.TestCase):
    def test_bpb_conversion(self):
        r=result_record(backend='pytorch',device='cpu',framework_version='x',parameter_count=10,train_seconds=1,validation_loss_nats=0.6931471805599453,seed=1,steps=2)
        self.assertAlmostEqual(r['validation_bpb'],1.0,places=7); self.assertTrue(validate_record(r))
    def test_compare(self):
        a=result_record(backend='a',device='x',framework_version='1',parameter_count=10,train_seconds=2,validation_loss_nats=1,seed=1,steps=1)
        b=result_record(backend='b',device='y',framework_version='1',parameter_count=10,train_seconds=1,validation_loss_nats=.5,seed=1,steps=1)
        c=compare_records(a,b); self.assertTrue(c['comparable']); self.assertAlmostEqual(c['speed_ratio_b_over_a'],.5)
if __name__=='__main__': unittest.main()
