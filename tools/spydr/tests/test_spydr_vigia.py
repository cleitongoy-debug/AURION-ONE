import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import SPYDR_VIGIA as s

class FakeResponse:
    def __init__(self,data):self.data=json.dumps(data).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data

class SpiderTests(unittest.TestCase):
    def test_incremental(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base'; root.mkdir()
            a=root/'AURION_arquivo.py'; a.write_text('abc')
            first,old=s.scan_roots([root],{})
            self.assertEqual(first['new'],1)
            same,_=s.scan_roots([root],old)
            self.assertEqual((same['new'],same['changed'],same['unchanged']),(0,0,1))
            a.write_text('abcde')
            newer,_=s.scan_roots([root],old)
            self.assertEqual(newer['changed'],1)
    def test_exclusion_of_secrets_and_system(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base';root.mkdir()
            (root/'AURION_senha.txt').write_text('private')
            (root/'LOCAL#SERVER.txt').write_text('key')
            (root/'Windows').mkdir();(root/'Windows'/'AURION.py').write_text('a')
            z,_=s.scan_roots([root],{})
            self.assertEqual(z['matched_files'],0)
    def test_reparse_symlink_not_followed(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base';root.mkdir()
            outside=Path(t)/'secret';outside.mkdir();(outside/'AURION.py').write_text('a')
            try:(root/'link').symlink_to(outside,target_is_directory=True)
            except OSError:self.skipTest('symlinks require developer mode on Windows')
            out,_=s.scan_roots([root],{})
            self.assertEqual(out['matched_files'],0)
    def test_limits_no_removed_counts(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base';root.mkdir()
            for i in range(10):(root/f'AURION_{i}.py').write_text('a')
            z,_=s.scan_roots([root],{'files':{'fake':{'sig':'1'}}},max_files=2)
            self.assertTrue(z['limited']);self.assertIsNone(z['removed_if_complete'])
    def test_github_main_and_pr(self):
        sha='a'*40
        def fetch(url):
            if url.endswith('commits/main'):return {'sha':'b'*40}
            return [{'number':52,'head':{'sha':sha}}]
        update,heads=s.github_updates({},fetch=fetch)
        self.assertEqual(update['changed_count'],2)
        same,_=s.github_updates(heads,fetch=fetch)
        self.assertEqual(same['changed_count'],0)
    def test_github_offline_never_confirms(self):
        def offline(_): raise OSError('offline')
        result,head=s.github_updates({'main':'safe'},fetch=offline)
        self.assertEqual(result['status'],'UNREACHABLE');self.assertEqual(head['main'],'safe')
    def test_bounded_allowlist(self):
        with self.assertRaises(ValueError):s.github_json('https://evil.example/api')
    def test_atomic_receipt_and_dedup(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base';root.mkdir()
            (root/'AURION.py').write_text('hello')
            out=Path(t)/'out'
            a=s.run([root],out,skip_network=True)
            b=s.run([root],out,skip_network=True)
            self.assertEqual(a['scan']['new'],1)
            self.assertEqual(b['scan']['unchanged'],1)
            self.assertTrue((out/'RESUMO_ATUAL.json').exists())
            self.assertEqual(len((out/'EVENTOS_SPYDR.jsonl').read_text().splitlines()),2)
    def test_roots_not_full_disk(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)
            self.assertTrue(s.safe_root(root))
            self.assertFalse(s.safe_root(Path('/')))
    def test_git_fixture_does_not_leak_titles(self):
        def fake(url):
            return {'sha':'c'*40} if url.endswith('commits/main') else [{'number':46,'title':'sensitive user content','head':{'sha':'d'*40}}]
        out,_=s.github_updates({},fetch=fake)
        self.assertNotIn('sensitive user content',json.dumps(out))

    def test_partial_scan_preserves_previous_entries(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
            root=Path(t)/'aurion_base';root.mkdir()
            for i in range(5):(root/f'AURION_{i}.py').write_text('x')
            first,state=s.scan_roots([root],{})
            self.assertEqual(first['matched_files'],5)
            partial,next_state=s.scan_roots([root],state,max_files=2)
            self.assertTrue(partial['limited'])
            self.assertEqual(len(next_state['files']),5)
            self.assertIsNone(partial['removed_if_complete'])
    def test_github_value_error_has_diagnostic_reason(self):
        def too_big(_):raise ValueError('GitHub response exceeded bound')
        result,_=s.github_updates({},fetch=too_big)
        self.assertEqual(result['reason'],'RESPONSE_TOO_LARGE')
        self.assertEqual(result['status'],'UNREACHABLE')

if __name__=='__main__':unittest.main()