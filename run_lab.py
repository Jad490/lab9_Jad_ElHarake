"""Run the handout commands on both versions; retain supplied-test failures."""
import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent
PHASES=[('cprofile',[('cprofile','python -m cProfile -s time profiler.py')]),
 ('line_profiler',[('line_profiler','python profiler_lineprofiler.py')]),
 ('tests',[('tests','python test_profiler.py')]),
 ('coverage',[('coverage_run','coverage run -m unittest discover'),('coverage_report','coverage report -m'),('coverage_html','coverage html'),('coverage_json','coverage json -o ../reports/{stage}/coverage.json')]),
 ('memory_profiler',[('memory_profiler','python -m memory_profiler profiler_memoryprofiler.py')])]
def environment():
 (ROOT/'reports').mkdir(exist_ok=True)
 (ROOT/'reports/environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ('line_profiler','memory_profiler','coverage','psutil')},'workloads':{'sleep_seconds':2,'slow_n':10000,'fast_n':100,'memory_n':10000000}},indent=2))
def save(stage,name,command,output,status,elapsed,capture='subprocess'):
 folder=ROOT/'reports'/stage;folder.mkdir(parents=True,exist_ok=True)
 (folder/(name+'.txt')).write_text(output)
 (folder/(name+'.json')).write_text(json.dumps({'command':command,'cwd':'lab9_Jad_ElHarake/'+stage,'exit_code':status,'wall_seconds':elapsed,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture':capture},indent=2))
def main():
 environment()
 for phase,commands in PHASES:
  for stage in ('before','after'):
   for name,command in commands:
    command=command.format(stage=stage);print(f'lab9_Jad_ElHarake/{stage} $ {command}',flush=True);start=time.perf_counter()
    result=subprocess.run(command.split(),cwd=ROOT/stage,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH']})
    save(stage,name,command,result.stdout,result.returncode,time.perf_counter()-start)
    print(result.stdout,end='',flush=True);print('Exit status:',result.returncode,flush=True)
    if result.returncode and name not in ('tests','coverage_run'): raise RuntimeError(command)
if __name__=='__main__':main()
