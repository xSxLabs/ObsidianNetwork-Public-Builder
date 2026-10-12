#!/usr/bin/env python3
"""CI-only extended server load fixture. Uses the frozen Build 106 JAR.
This tests network topology churn, NOT verified active item/fluid throughput.
"""
import runpy
from pathlib import Path
# Execute the proven five-scale benchmark first; it defines the connected RCON client.
state=runpy.run_path(str(Path(__file__).with_name('benchmark.py')))
r=state['r']
import json,time,statistics,re
phases=[]
for kind in ('item_cable','fluid_cable'):
    for n in (128,512,1024):
        coords=[(i%64, i//64) for i in range(n)]
        errors=[]
        start=time.monotonic()
        for x,z in coords:
            ans=r.cmd(f'setblock {x} 70 {z} obsidiannetwork:{kind}')
            if 'Unknown' in ans or 'unknown' in ans or 'Failed' in ans:
                errors.append(ans)
        if errors:
            raise RuntimeError(f'{kind} placement errors: {errors[:3]}')
        for x,z in coords[::4]:
            r.cmd(f'setblock {x} 70 {z} minecraft:air')
            ans=r.cmd(f'setblock {x} 70 {z} obsidiannetwork:{kind}')
            if 'Unknown' in ans or 'unknown' in ans:
                raise RuntimeError(f'{kind} topology rebuild failed: {ans}')
        samples=[]
        for _ in range(8):
            q=r.cmd('tick query')
            m=re.search(r'Average time per tick:\s*([0-9]+(?:[.,][0-9]+)?)',q,re.I)
            if not m: raise RuntimeError('MSPT parse failed: '+q)
            samples.append(float(m.group(1).replace(',','.')))
            time.sleep(3)
        phase={'kind':kind,'cables':n,'rebuilds':len(coords[::4]),
               'avg_mspt':round(statistics.mean(samples),3),
               'max_sample_mspt':max(samples),'samples_mspt':samples,
               'elapsed_seconds':round(time.monotonic()-start,2)}
        phases.append(phase)
        print('EXTENDED_RESULT',json.dumps(phase),flush=True)
with open('extended-stress-results.json','w') as f:
    json.dump({'method':'frozen Build 106 server cable placement and topology churn',
               'active_transfers_verified':False,'phases':phases},f,indent=2)
