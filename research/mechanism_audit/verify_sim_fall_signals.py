"""Read-only validation of saved cases, including quaternion/gravity agreement."""
import json
import hashlib
from pathlib import Path
import numpy as np
import torch

OUT=Path(__file__).resolve().parent/'sim_fall_filter'
torch.set_num_threads(2)
rows=[]
for path in sorted(OUT.glob('m*.pt')):
    if '_smoke' in path.name:continue
    data=torch.load(path,map_location='cpu',weights_only=True)
    assert data['metadata']['complete']
    assert all(torch.isfinite(v).all() for v in data.values() if isinstance(v,torch.Tensor))
    qw,qx,qy,qz=data['quat'].numpy().transpose(2,0,1)
    expected=np.stack([2*(qw*qy-qx*qz),-2*(qw*qx+qy*qz),-1+2*(qx*qx+qy*qy)],axis=-1)
    error=float(np.abs(expected-data['gravity'].numpy()).max())
    assert error<1e-4
    for env in range(16):
        active=data['active'][:,env];n=int(active.sum())
        assert active[:n].all() and not active[n:].any() and data['done'][n-1,env]
    rows.append({'file':path.name,'quat_gravity_max_error':error,'frames':data['metadata']['frames']})
print(json.dumps({'saved_cases':len(rows),'complete':len(rows)==12,'validated':rows},indent=2))
if len(rows)==12:
    results=json.loads((OUT/'results.json').read_text())
    assert results['complete'] and len(results['cases'])==12 and len(results['episodes'])==192
    assert len({(r['model'],r['seed'],r['scenario'],r['env']) for r in results['episodes']})==192
    for case in results['cases']:
        meta=case['metadata']
        name=f"m{case['model']}_s{case['seed']}_{case['scenario']}.pt"
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==case['sha256']
        assert hashlib.sha256((OUT.parent/'SIM_FALL_FILTER_PROTOCOL.md').read_bytes()).hexdigest()==meta['protocol_sha256']
    for name,expected in results['provenance']['files_sha256'].items():
        assert hashlib.sha256((OUT.parent/name).read_bytes()).hexdigest()==expected
    validation={'complete':True,'cases':12,'first_episodes':192,'finite':True,
                'unique':True,'source_and_protocol_hashes_verified':True,'signal_checks':rows}
    (OUT/'completion_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    inventory=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact_inventory.json']
    (OUT/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
