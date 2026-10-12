#!/usr/bin/env python3
"""Real dedicated-server MSPT load test using Minecraft RCON.
Measures loaded item-cable grids and adjacent barrel inventories.
Does NOT claim to populate Network Storage's controller/drive API.
"""
import json,re,socket,struct,time,statistics,sys
HOST='127.0.0.1'; PORT=25575; PASSWORD='stress106localonly'
class Rcon:
 def __init__(self):
  self.s=socket.create_connection((HOST,PORT),timeout=15);self.s.settimeout(30);self.seq=0
  self.send(3,PASSWORD)
  if self.recv()[0]==-1:raise RuntimeError('RCON authentication failed')
 def send(self,typ,msg):
  self.seq+=1
  body=struct.pack('<ii',self.seq,typ)+msg.encode()+b'\0\0'
  self.s.sendall(struct.pack('<i',len(body))+body)
  return self.seq
 def read(self,n):
  b=b''
  while len(b)<n:
   c=self.s.recv(n-len(b))
   if not c:raise ConnectionError('RCON closed')
   b+=c
  return b
 def recv(self):
  size=struct.unpack('<i',self.read(4))[0]
  if not 10<=size<=1024*1024:raise ValueError('Invalid RCON frame')
  data=self.read(size)
  return struct.unpack('<ii',data[:8])[0],data[8:-2].decode(errors='replace')
 def cmd(self,msg):
  id=self.send(2,msg)
  for _ in range(8):
   got,body=self.recv()
   if got==id:return body
  raise RuntimeError('RCON response mismatch')
def connect():
 for i in range(240):
  try:
   r=Rcon()
   if 'Unknown' not in r.cmd('list'):return r
  except (OSError,ValueError,ConnectionError):pass
  time.sleep(2)
 raise TimeoutError('NeoForge server did not become RCON-ready within 8 minutes')
r=connect()
print('STRESSTEST BUILD 106: dedicated NeoForge server RCON ready',flush=True)
print('Version:',r.cmd('version'),flush=True)
print('World setup:',r.cmd('forceload add 0 0 63 63'),flush=True)
print('Keep day:',r.cmd('gamerule doDaylightCycle false'),flush=True)
# 64x64 flat connected ITEM cable plane; adjacent barrels store real item stacks.
# We grow monotonically and keep all four chunks loaded.
scenarios=[(100,25),(500,125),(1000,250),(2000,500),(4000,1000)]
results=[]
for cables,barrels in scenarios:
 print('POPULATING',cables,'item cables',barrels,'barrels',flush=True)
 for idx in range(cables):
  x=idx%64;z=idx//64
  if idx>= (results[-1]['cables'] if results else 0):
   ans=r.cmd(f'setblock {x} 64 {z} obsidiannetwork:item_cable')
   if 'Unknown' in ans or 'unknown' in ans or 'Failed to load' in ans:
    raise RuntimeError('Cannot place actual mod item cable: '+ans)
 for idx in range(barrels):
  if idx < (results[-1]['barrels'] if results else 0):continue
  x=idx%64;z=idx//64
  # Real inventories, filled with 27 item stacks; item counts not unique item types.
  itemtags=','.join('{Slot:'+str(j)+'b,id:"minecraft:stone",count:64}' for j in range(27))
  ans=r.cmd(f'setblock {x} 65 {z} minecraft:barrel[facing=up]{{Items:[{itemtags}]}}')
  if 'Unknown' in ans or 'unknown' in ans:raise RuntimeError('Inventory setup failed: '+ans)
 time.sleep(15)
 samples=[]
 for _ in range(6):
  response=r.cmd('tick query')
  match=re.search(r'Average time per tick:\\s*([0-9]+(?:[.,][0-9]+)?)',response,re.I)
  if not match:
   match=re.search(r'([0-9]+(?:[.,][0-9]+)?)\\s*ms(?:pt)?',response,re.I)
  if not match:raise RuntimeError('Unable to parse server MSPT from /tick query: '+response)
  samples.append(float(match.group(1).replace(',','.')))
  time.sleep(5)
 avg=statistics.mean(samples)
 result={'cables':cables,'barrels':barrels,'stored_stacks':barrels*27,'stored_items':barrels*27*64,'avg_mspt':round(avg,3),'max_sample_mspt':round(max(samples),3),'theoretical_tps_at_avg_mspt':round(min(20,1000/avg),2) if avg>0 else 20,'samples_mspt':samples}
 results.append(result)
 print('RESULT',json.dumps(result),flush=True)
with open('stress-results.json','w') as f:json.dump({'method':'NeoForge 26.1.2.106 /tick query; real loaded item cables and vanilla barrel inventories; no verified active transfers or storage controller', 'scenarios':results},f,indent=2)
print('DONE. Results are loaded-world tick cost, not active-transfer throughput.',flush=True)
