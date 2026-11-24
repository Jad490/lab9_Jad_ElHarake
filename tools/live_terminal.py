"""Live, task-only PTY terminal for native browser screenshots (localhost only)."""
import fcntl
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import threading
import time
import pyte
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run_lab import PHASES,environment,save
ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
LOCK=threading.Lock();ADVANCE=threading.Event()
STATE={'phase':'starting','stage':'before','status':'starting','lines':[],'index':0}
HTML='''<!doctype html><html><head><meta charset="utf-8"><title>lab9_Jad_ElHarake — Live Terminal</title><style>html,body{margin:0;background:#10151b;color:#e6edf3;font-family:Menlo,monospace}header{padding:9px 15px;border-bottom:1px solid #45515d;display:flex;align-items:center;gap:20px}h1{font-size:15px;margin:0}#status{font-size:11px;color:#b7d8f2}button{margin-left:auto;padding:6px 12px;cursor:pointer}pre{font-family:Menlo,monospace;font-size:10.5px;line-height:1.24;margin:10px 15px;white-space:pre;tab-size:4}</style></head><body><header><h1>lab9_Jad_ElHarake | Live PTY Terminal</h1><span id="status"></span><button id="next" disabled>Continue to next run</button></header><pre id="screen"></pre><script>const b=document.getElementById('next');b.onclick=async()=>{b.disabled=true;await fetch('/advance',{method:'POST'})};async function refresh(){try{const s=await(await fetch('/state',{cache:'no-store'})).json();document.getElementById('status').textContent=s.stage.toUpperCase()+' | '+s.phase+' | '+s.status;document.getElementById('screen').textContent=s.lines.join('\\n');b.disabled=s.status!=='complete';}catch(e){}}setInterval(refresh,300);refresh();</script></body></html>'''
def update(**values):
 with LOCK:
  STATE.update(values)
  (ROOT/'reports'/('live_state_'+str(PORT)+'.json')).write_text(json.dumps({k:v for k,v in STATE.items() if k!='lines'}))
class Terminal:
 def __init__(self,stage):
  self.stage=stage;self.raw=bytearray();self.screen=pyte.Screen(160,80);self.stream=pyte.Stream(self.screen)
  self.prompt=re.compile(re.escape('lab9_Jad_ElHarake/'+stage+' [exit=')+r'(\d+)\] \$ $')
  master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',80,160,0,0));self.master=master
  self.process=subprocess.Popen(['/bin/bash','--noprofile','--norc','-i'],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT/stage,start_new_session=True,env={**os.environ,'PS1':'lab9_Jad_ElHarake/'+stage+' [exit=$?] $ ','TERM':'xterm-256color','PYTHONUNBUFFERED':'1','PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH']})
  os.close(slave);self.read();os.write(master,b'clear\n');self.read()
 def publish_screen(self):
  lines=self.screen.display
  while lines and not lines[-1].strip():lines.pop()
  with LOCK:STATE['lines']=lines
 def read(self):
  chunk=bytearray();start=time.monotonic()
  while time.monotonic()-start<1800:
   ready,_,_=select.select([self.master],[],[],0.3)
   if ready:
    part=os.read(self.master,65536)
    if not part:raise RuntimeError('PTY closed')
    chunk.extend(part);self.raw.extend(part);self.stream.feed(part.decode('utf-8',errors='replace'));self.publish_screen()
    plain=ANSI.sub('',chunk.decode('utf-8',errors='replace')).replace('\r','');match=self.prompt.search(plain)
    if match:return bytes(chunk),plain,match
   elif self.process.poll() is not None:raise RuntimeError('Shell exited')
  raise TimeoutError('Command timed out after 30 minutes')
 def run(self,name,command):
  start=time.perf_counter();os.write(self.master,(command+'\n').encode());raw,plain,prompt=self.read()
  output=plain.split('\n',1)[1];output=output[:output.rfind(prompt.group(0))];status=int(prompt.group(1))
  save(self.stage,name,command,output,status,time.perf_counter()-start,'live PTY in browser; native screenshot captured separately')
  (ROOT/'reports/transcripts'/f'{self.stage}_{name}.tty').write_bytes(raw);print(f'{self.stage}/{name}: exit {status}',flush=True)
  if status and name not in ('tests','coverage_run'):raise RuntimeError(command)
 def close(self):
  self.process.kill()
  os.close(self.master)

def worker():
 try:
  environment();(ROOT/'reports/transcripts').mkdir(exist_ok=True);index=0
  for phase,commands in PHASES:
   for stage in ('before','after'):
    index+=1
    if index<START_INDEX:continue
    if index>END_INDEX:break
    update(index=index,phase=phase,stage=stage,status='running');terminal=Terminal(stage)
    for name,command in commands:terminal.run(name,command.format(stage=stage))
    update(status='complete');ADVANCE.wait();ADVANCE.clear();terminal.close()
  update(status='all_done')
 except Exception as exc:
  update(status='error',error=str(exc));raise
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/':content=HTML.encode();mime='text/html; charset=utf-8'
  elif self.path=='/state':
   with LOCK:content=json.dumps(STATE).encode()
   mime='application/json'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(content)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(content)
 def do_POST(self):
  if self.path!='/advance':self.send_error(404);return
  with LOCK:allowed=STATE['status']=='complete'
  if allowed:ADVANCE.set()
  self.send_response(204 if allowed else 409);self.end_headers()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--start',type=int,default=1);parser.add_argument('--port',type=int,default=8769);parser.add_argument('--end',type=int,default=10);args=parser.parse_args();START_INDEX=args.start;END_INDEX=args.end;PORT=args.port
 environment();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);(ROOT/'reports'/('server_'+str(args.port)+'.pid')).write_text(str(os.getpid()));threading.Thread(target=worker,daemon=True).start();print('Live homework terminal: http://127.0.0.1:'+str(args.port),flush=True);server.serve_forever()
