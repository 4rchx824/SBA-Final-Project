"""Freshness must survive copying but reject mixed or incomplete bundles."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analytics'))
from check_lighting_freshness import check_freshness, snapshot, digest, RECEIPT


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'original'
        files = {
            'outputs/lighting/run_manifest.json': json.dumps({'sources': {'input.csv': 'unused'}}),
            'outputs/lighting/scenario_intervals.csv.gz': 'details',
            'outputs/lighting/scenario_sensitivity.csv': 'summary',
            'input.csv': 'input',
            'analytics/lighting/tests/verify_lighting_outputs.py': 'audit',
            'analytics/model.py': 'model',
        }
        for relative, value in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        (self.root / RECEIPT).write_text(json.dumps({'status': 'passed', 'file_sha256': snapshot(self.root)}))

    def test_complete_bundle_can_move_between_machines(self):
        target = Path(self.temp.name) / 'remote'
        shutil.copytree(self.root, target)
        self.assertEqual(check_freshness(target)['status'], 'passed')

    def test_notebook_execution_metadata_does_not_change_code_digest(self):
        path = self.root / 'notebook.ipynb'
        cell = {'cell_type': 'code', 'source': ['print(1)'], 'outputs': []}
        path.write_text(json.dumps({'cells': [cell]}))
        before = digest(path)
        cell['outputs'] = [{'text': '1'}]
        path.write_text(json.dumps({'cells': [cell]}))
        self.assertEqual(before, digest(path))
        cell['source'] = ['print(2)']
        path.write_text(json.dumps({'cells': [cell]}))
        self.assertNotEqual(before, digest(path))

    def test_changed_source_summary_or_details_rejected(self):
        for relative in ['input.csv', 'analytics/model.py',
                         'outputs/lighting/scenario_sensitivity.csv',
                         'outputs/lighting/scenario_intervals.csv.gz']:
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'Missing or changed'):
                    check_freshness(self.root)
                path.write_bytes(original)

    def test_missing_ignored_file_rejected(self):
        (self.root / 'outputs/lighting/scenario_intervals.csv.gz').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or changed'):
            check_freshness(self.root)

    def test_old_or_interrupted_receipt_rejected(self):
        for receipt in [{'status': 'passed'}, {'status': 'in_progress'}]:
            (self.root / RECEIPT).write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'No hash-backed'):
                check_freshness(self.root)


if __name__ == '__main__':
    unittest.main()
