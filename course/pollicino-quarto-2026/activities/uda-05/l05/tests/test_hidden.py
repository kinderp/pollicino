import unittest
from main import result_record, validate_record, compare_records
class TestBenchmarkHidden(unittest.TestCase):
    def test_missing_field(self):
        with self.assertRaises(ValueError): validate_record({'backend':'x'})
    def test_param_mismatch(self):
        a=result_record(backend='a',device='x',framework_version='1',parameter_count=10,train_seconds=1,validation_loss_nats=1,seed=1,steps=1)
        b=result_record(backend='b',device='x',framework_version='1',parameter_count=11,train_seconds=1,validation_loss_nats=1,seed=1,steps=1)
        self.assertFalse(compare_records(a,b)['comparable'])
if __name__=='__main__': unittest.main()
