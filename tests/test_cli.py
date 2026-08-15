from pollicino.compression.cli import main
def test_cli_roundtrip(tmp_path):
 source=tmp_path/'input.bin'; packed=tmp_path/'output.pol'; restored=tmp_path/'restored.bin'; source.write_bytes(b'POLLICINO '*300); assert main(['compress',str(source),str(packed),'--mode','static'])==0; assert main(['restore',str(packed),str(restored)])==0; assert restored.read_bytes()==source.read_bytes()
