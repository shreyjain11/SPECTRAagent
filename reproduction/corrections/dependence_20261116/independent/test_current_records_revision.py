"""Regression checks for revision-bound AlphaMissense metadata.

Uses small temporary copies of the current six records and their referenced
notebooks/receipt chain. No source repository files are modified by these tests.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

REPRODUCTION=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('current_records_under_test',REPRODUCTION/'corrections/alphamissense/verify_current_records.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class ScientificSummaryMetadataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fixture_temp=tempfile.TemporaryDirectory(prefix='spectra-metadata-fixture-')
  cls.fixture=Path(cls.fixture_temp.name);wanted=set()
  def add(relative):
   wanted.add(relative);return read(REPRODUCTION/relative)
  for identifier in module.EXPECTED_PRESERVED_SHA256:
   record=add('analyses/'+identifier+'.json');current=record['current_inline_analysis']
   add(current['evidence']['notebook']);add(current['evidence']['statistical_result']['path'])
   receipt=add(record['inline_implementation']['execution_evidence'])
   while receipt.get('scientific_revision'):
    revision=receipt['scientific_revision'];add(revision['record']['path'])
    receipt=add(revision['previous_execution_evidence']['path'])
   presentation=receipt.get('presentation_revision',{}).get('correction_record')
   if presentation:
    change=add(presentation['path']);snapshot=change.get('previous_inline_implementation')
    if snapshot:add(snapshot['path'])
  for relative in wanted:
   target=cls.fixture/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPRODUCTION/relative,target)
 @classmethod
 def tearDownClass(cls):cls.fixture_temp.cleanup()
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='spectra-metadata-test-');self.root=Path(self.temp.name)
  shutil.copytree(self.fixture,self.root,dirs_exist_ok=True)
  self.record_path=self.root/'analyses/am-opus-r1/test-01.json';self.record=read(self.record_path)
 def tearDown(self):self.temp.cleanup()
 def assertRejected(self):
  with self.assertRaises(AssertionError):module.verify(self.root)
 def test_accepts_all_six_current_records(self):
  self.assertEqual(module.verify(self.root),list(module.EXPECTED_PRESERVED_SHA256))
 def test_rejects_changed_current_numerical_result(self):
  current=self.record['current_inline_analysis'];current['curve']['reported_result']['primary_contrasts'][0]['mean']+=0.01
  write(self.record_path,self.record);self.assertRejected()
 def test_rejects_changed_current_comparator(self):
  current=self.record['current_inline_analysis'];current['insight']['comparator_contrasts'][0]['low']-=0.05
  write(self.record_path,self.record);self.assertRejected()
 def test_rejects_tampered_summary_bytes(self):
  item=self.record['current_inline_analysis']['evidence']['statistical_result'];p=self.root/item['path'];p.write_bytes(p.read_bytes()+b'\n')
  self.assertRejected()
 def test_rejects_tampered_summary_hash(self):
  self.record['current_inline_analysis']['evidence']['statistical_result']['sha256']='0'*64
  write(self.record_path,self.record);self.assertRejected()
 def test_rejects_rehashed_summary_not_bound_in_correction_receipt(self):
  item=self.record['current_inline_analysis']['evidence']['statistical_result'];p=self.root/item['path'];summary=read(p)
  summary['am-opus-r1/test-01']['reported_result']['primary_contrasts'][0]['mean']+=0.01
  write(p,summary);item['sha256']=digest(p)
  self.record['current_inline_analysis']['curve']['reported_result']=copy.deepcopy(summary['am-opus-r1/test-01']['reported_result'])
  write(self.record_path,self.record)
  with self.assertRaisesRegex(AssertionError,'not a recorded correction output'):module.verify(self.root)
 def test_rejects_changed_historical_scientific_metadata(self):
  self.record['curve']['aggregation_and_uncertainty']='Altered historical analysis'
  write(self.record_path,self.record)
  with self.assertRaisesRegex(AssertionError,'historical fields changed'):module.verify(self.root)
 def test_rejects_tampered_archived_receipt(self):
  receipt=read(self.root/self.record['inline_implementation']['execution_evidence'])
  previous=self.root/receipt['scientific_revision']['previous_execution_evidence']['path'];previous.write_bytes(previous.read_bytes()+b'\n')
  self.assertRejected()

if __name__=='__main__':unittest.main(verbosity=2)
