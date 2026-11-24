"""Validate handout fidelity and artifacts; never treat failed tests as passed."""
import ast
import hashlib
from html.parser import HTMLParser
import json
import sys
from pathlib import Path
from zipfile import ZipFile
from docx import Document
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def function(path,name):
 tree=ast.parse(path.read_text())
 return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)

def body(path,name):
 return ast.dump(ast.Module(body=function(path,name).body,type_ignores=[]),include_attributes=False)

class Links(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('src','href') and value and not value.startswith(('http','#','data:','mailto:')):
    self.paths.append(value.split('#')[0].split('?')[0])

def main():
 from build_report import SHOTS
 from run_lab import PHASES
 checks=[];test_outcomes={}
 for stage in ('before','after'):
  folder=ROOT/stage
  for name in ('profiler.py','profiler_lineprofiler.py','profiler_memoryprofiler.py','test_profiler.py'):
   ast.parse((folder/name).read_text())
  for name in ('slow_function','memory_intensive_function'):
   expected=body(ROOT/'before/profiler.py',name)
   for file in ('profiler.py','profiler_lineprofiler.py','profiler_memoryprofiler.py'):
    assert body(folder/file,name)==expected,(stage,file,name)
  fast='fast_function' if stage=='before' else 'optimized_fast_function'
  for file in ('profiler_lineprofiler.py','profiler_memoryprofiler.py'):
   assert body(folder/file,fast)==body(folder/'profiler.py',fast)
  if stage=='after':
   expected=ast.dump(ast.parse('return sum(i**2 for i in range(100))'),include_attributes=False)
   assert body(folder/'profiler.py',fast)==expected
  tests=(folder/'test_profiler.py').read_text();tree=ast.parse(tests)
  methods=[x.name for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')]
  assert sorted(methods)==['test_fast_function','test_memory_intensive_function','test_slow_function']
  assert 'start_time = time.time()' in tests
  assert 'self.assertGreater(mem_usage_after[0], mem_usage_before[0]' in tests
  assert 'self.assertGreater(duration, 2,' in tests and 'self.assertLess(duration, 1,' in tests and 'self.assertLess(duration, 5,' in tests
  assert not (folder/'.coveragerc').exists()
  for phase,commands in PHASES:
   for name,expected_command in commands:
    p=ROOT/'reports'/stage
    meta=json.loads((p/(name+'.json')).read_text());output=(p/(name+'.txt')).read_text()
    assert meta['command']==expected_command.format(stage=stage)
    if name in ('tests','coverage_run'):
     assert 'Ran 3 tests' in output
     if meta['exit_code']==0:assert '\nOK' in output
     else:assert 'FAILED (' in output and 'Traceback' in output
     test_outcomes[stage+'/'+name]={'exit_code':meta['exit_code'],'reported_as':'PASS' if meta['exit_code']==0 else 'FAIL'}
    else:assert meta['exit_code']==0,(stage,name)
  memory=(ROOT/'reports'/stage/'memory_profiler.txt').read_text()
  assert '10000001' in memory and '10000000' in memory
  cov=json.loads((ROOT/'reports'/stage/'coverage.json').read_text())
  assert {'profiler.py','test_profiler.py'}<=set(cov['files'])
  assert cov['files']['profiler.py']['summary']['excluded_lines']==0
  assert cov['files']['profiler.py']['missing_lines'],'The exact discovery run should leave main/CLI statements unexecuted.'
  for page in (folder/'htmlcov').glob('*.html'):
   parser=Links();parser.feed(page.read_text())
   for path in parser.paths:assert (page.parent/path).exists(),(stage,page,path)
  checks.append(stage+': original workloads, exact example, three supplied tests/thresholds/assertions, default coverage, real outputs, HTML assets')
 captures=json.loads((ROOT/'reports/screenshots/capture_manifest.json').read_text())
 assert {x['filename'] for x in captures}=={n for n,_ in SHOTS}
 hashes=[]
 for item in captures:
  assert item['method']=='native_screenshot_live_terminal'
  p=ROOT/'reports/screenshots'/item['filename']
  with Image.open(p) as im:im.verify()
  digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==item['sha256'];hashes.append(digest)
 assert len(set(hashes))==10
 report=ROOT/'lab9_Jad_ElHarake.docx'
 with ZipFile(report) as z:assert z.testzip() is None
 doc=Document(report);assert len(doc.inline_shapes)==10
 text='\n'.join(p.text for p in doc.paragraphs)
 assert 'No failed assertion was replaced' in text and 'sum(i**2 for i in range(100))' in text
 assert (ROOT/'lab9_Jad_ElHarake_GitHub.txt').read_text().strip()=='https://github.com/Jad490/lab9_Jad_ElHarake'
 checks.append('Ten native live-terminal screenshots and one Word document with measured outputs and analysis')
 result={'status':'passed','meaning':'Handout fidelity and artifact checks passed; supplied test outcomes remain separate.','checks':checks,'supplied_test_outcomes':test_outcomes,'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
 (ROOT/'reports/validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
