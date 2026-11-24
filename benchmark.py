"""Compare the original loop and the handout's exact generator example."""
import importlib.util
import json
from pathlib import Path
import statistics
import timeit
ROOT=Path(__file__).resolve().parent

def load(stage):
 spec=importlib.util.spec_from_file_location(stage,ROOT/stage/'profiler.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

def main():
 before,after=load('before'),load('after')
 results={'calls_per_repeat':20000,'repeats':7,'functions':{}}
 for name,function in [('baseline_loop',before.fast_function),('handout_generator',after.optimized_fast_function)]:
  assert function()==328350
  samples=[t/20000 for t in timeit.repeat(function,number=20000,repeat=7)]
  results['functions'][name]={'seconds_per_call':samples,'median_seconds':statistics.median(samples),'min_seconds':min(samples),'max_seconds':max(samples)}
 results['median_speedup_ratio']=results['functions']['baseline_loop']['median_seconds']/results['functions']['handout_generator']['median_seconds']
 (ROOT/'reports/benchmark.json').write_text(json.dumps(results,indent=2))
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
