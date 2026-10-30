import importlib.util,unittest,tempfile,hashlib,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('switch',Path(__file__).with_name('guarded_proxy_switch.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class NarrowSwitch(unittest.TestCase):
 def test_roundtrip_and_unrelated_routes_preserved(self):
  text='other.example {\n reverse_proxy 127.0.0.1:8091\n}\nsite-intelligence-api.sustainablecatalyst.com {\n\treverse_proxy 127.0.0.1:8091\n}\n'
  changed=m.patch(text,8091,18091);self.assertIn('other.example {\n reverse_proxy 127.0.0.1:8091',changed);self.assertEqual(m.patch(changed,18091,8091),text)
 def test_duplicate_hostname_refused(self):
  block='site-intelligence-api.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:8091\n}\n'
  with self.assertRaises(ValueError):m.patch(block+block,8091,18091)
 def test_wrong_upstream_refused(self):
  with self.assertRaises(ValueError):m.patch('site-intelligence-api.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:9999\n}\n',8091,18091)
 def test_port_prefix_not_treated_as_expected_port(self):
  with self.assertRaises(ValueError):m.patch('site-intelligence-api.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:80910\n}\n',8091,18091)
 def test_multiple_upstreams_refused(self):
  with self.assertRaises(ValueError):m.patch('site-intelligence-api.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:8091\n reverse_proxy 127.0.0.1:1234\n}\n',8091,18091)
class SnapshotGuards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.root.chmod(0o700);self.expected={}
  for n in m.STATE_PATHS:
   p=self.root/n;p.parent.mkdir(exist_ok=True);p.write_bytes(b'SYNTHETIC');self.expected[n]=hashlib.sha256(b'SYNTHETIC').hexdigest()
 def tearDown(self):self.tmp.cleanup()
 def test_complete_snapshot(self):m.verify_snapshot(self.root,self.expected)
 def test_wrong_hash(self):
  (self.root/next(iter(self.expected))).write_bytes(b'changed')
  with self.assertRaises(ValueError):m.verify_snapshot(self.root,self.expected)
 def test_wrong_scope(self):
  expected=dict(self.expected);expected.pop(next(iter(expected)))
  with self.assertRaises(ValueError):m.verify_snapshot(self.root,expected)
 def test_symlink_refused(self):
  p=self.root/next(iter(self.expected));p.unlink();p.symlink_to('/etc/hosts')
  with self.assertRaises(ValueError):m.verify_snapshot(self.root,self.expected)
if __name__=='__main__':unittest.main()


def test_corrected_frontend_patch_and_inverse_preserve_other_hosts():
    text="intelligence.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:8096\n}\nworkspace.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:8088\n}\n"
    new=m.patch_frontend(text,8096,18096)
    assert "127.0.0.1:8088" in new
    assert m.patch_frontend(new,18096,8096)==text


def test_corrected_frontend_wrong_upstream_refuses():
    import pytest
    with pytest.raises(ValueError):m.patch_frontend("intelligence.sustainablecatalyst.com {\n reverse_proxy 127.0.0.1:8097\n}\n",8096,18096)
