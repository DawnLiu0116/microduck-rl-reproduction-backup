"""Paired offline BC mechanism screen; no closed-loop or poisoning claims."""
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn
from rsl_rl.modules import EmpiricalNormalization

OUT=Path(__file__).resolve().parent/'normalization_pilot'

def rotate(x,degrees):
    z=x.clone();a=math.radians(float(degrees));c,s=math.cos(a),math.sin(a)
    for i in (0,3):
        z[:,i]=c*x[:,i]+s*x[:,i+2]
        z[:,i+2]=-s*x[:,i]+c*x[:,i+2]
    return z

def save(result):
    tmp=OUT/'results.tmp';tmp.write_text(json.dumps(result,indent=2));tmp.replace(OUT/'results.json')

def main():
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    target=OUT/'results.json'
    result=json.loads(target.read_text()) if target.exists() else {'complete':False,'rows':[],'scope':'offline BC mechanism screen only'}
    done={(r['collection_seed'],r['amplitude'],r['init_seed'],r['normalization'],r['order']) for r in result['rows']}
    for collection in (4004,5005,6006):
        data=torch.load(OUT/f'teacher_seed{collection}.pt',map_location='cpu',weights_only=True)
        x=data['x'][:,:48].reshape(-1,61);y=data['y'][:,:48].reshape(-1,14)
        tx=data['x'][:,48:].reshape(-1,61);ty=data['y'][:,48:].reshape(-1,14)
        tests={str(a):rotate(tx,a) for a in (0,-6,6)}
        calibration=EmpiricalNormalization(61);calibration.update(x)
        rng=np.random.default_rng(901)
        ids=torch.tensor(rng.permutation(len(x)).reshape(256,192))
        orders={'random':rng.permutation(256).tolist(),'ascending':list(range(256)),'descending':list(range(255,-1,-1))}
        assert all(sorted(order)==list(range(256)) for order in orders.values())
        for amplitude in (0,6):
            angles=np.repeat(np.linspace(-amplitude,amplitude,8),32)
            bx=[rotate(x[ids[i]],angles[i]) for i in range(256)]
            by=[y[ids[i]] for i in range(256)]
            ledger={'sample_ids':ids.tolist(),'angles':angles.tolist(),'orders':orders,'same_multiset':True,'data_sha256':hashlib.sha256((OUT/f'teacher_seed{collection}.pt').read_bytes()).hexdigest()}
            (OUT/f'ledger_{collection}_{amplitude}.json').write_text(json.dumps(ledger))
            for seed in (42,123,2026):
                torch.manual_seed(seed)
                initial=nn.Sequential(nn.Linear(61,128),nn.ELU(),nn.Linear(128,64),nn.ELU(),nn.Linear(64,14))
                for mode in ('frozen','cumulative'):
                    for order_name,order in orders.items():
                        key=(collection,amplitude,seed,mode,order_name)
                        if key in done:continue
                        model=copy.deepcopy(initial);norm=copy.deepcopy(calibration)
                        optimizer=torch.optim.Adam(model.parameters(),lr=.001)
                        trajectory=[]
                        def update(a,b):
                            optimizer.zero_grad();loss=(model(norm(a))-b).square().mean();loss.backward();optimizer.step()
                            if mode=='cumulative':norm.update(a)
                        def snapshot(step):
                            trajectory.append({'step':step,'count':int(norm.count),'mean':norm.mean.tolist(),'std':norm.std.tolist()})
                        def metrics():
                            with torch.no_grad():
                                return {name:float((model(norm(t))-ty).square().mean()) for name,t in tests.items()}
                        snapshot(0)
                        for j,i in enumerate(order):
                            update(bx[i],by[i])
                            if (j+1)%32==0:snapshot(j+1)
                        measured={'0':metrics()}
                        for j in range(256):
                            update(x[ids[j]],y[ids[j]])
                            if (j+1)%32==0:snapshot(256+j+1)
                            if j+1 in (64,256):measured[str(j+1)]=metrics()
                        assert all(math.isfinite(v) for m in measured.values() for v in m.values())
                        name=f'{collection}_a{amplitude}_s{seed}_{mode}_{order_name}'
                        torch.save({'model':model.state_dict(),'normalizer':norm.state_dict(),'eps':norm.eps,'optimizer':optimizer.state_dict()},OUT/f'{name}.pt')
                        (OUT/f'{name}_trajectory.json').write_text(json.dumps(trajectory))
                        row={'collection_seed':collection,'amplitude':amplitude,'init_seed':seed,'normalization':mode,'order':order_name,'recovery_mse':measured,'final_count':int(norm.count),'state_file':f'{name}.pt'}
                        result['rows'].append(row);done.add(key);save(result)
                        print(f'PILOT {len(result["rows"])}/108 {name} worst256={max(measured["256"].values()):.6g}',flush=True)
    assert len(done)==108 and len(result['rows'])==108
    result['complete']=True;save(result)
    contrasts=[]
    lookup={(r['collection_seed'],r['amplitude'],r['init_seed'],r['normalization'],r['order']):r for r in result['rows']}
    for collection in (4004,5005,6006):
        for seed in (42,123,2026):
            for order in ('ascending','descending'):
                for recovery in ('0','64','256'):
                    values={}
                    for amp in (0,6):
                        for mode in ('frozen','cumulative'):
                            a=max(lookup[(collection,amp,seed,mode,order)]['recovery_mse'][recovery].values())
                            b=max(lookup[(collection,amp,seed,mode,'random')]['recovery_mse'][recovery].values())
                            values[f'{amp}_{mode}']=math.log(a/b)
                    excess=values['6_cumulative']-values['6_frozen']
                    zero=values['0_cumulative']-values['0_frozen']
                    contrasts.append({'collection_seed':collection,'init_seed':seed,'order':order,'recovery':int(recovery),'log_ratios':values,'normalization_excess_log_ratio':excess,'zero_control_excess_log_ratio':zero,'difference_minus_zero':excess-zero})
    summary={'complete':True,'runs':108,'finite':True,'paired_contrasts':contrasts,'groups':[]}
    for order in ('ascending','descending'):
        for recovery in (0,64,256):
            subset=[r for r in contrasts if r['order']==order and r['recovery']==recovery]
            summary['groups'].append({'order':order,'recovery':recovery,'pairs':len(subset),'mean_extra_log_ratio':float(np.mean([r['normalization_excess_log_ratio'] for r in subset])),'mean_zero_control_log_ratio':float(np.mean([r['zero_control_excess_log_ratio'] for r in subset])),'mean_difference_minus_zero':float(np.mean([r['difference_minus_zero'] for r in subset])),'positive_pairs':sum(r['difference_minus_zero']>0 for r in subset),'per_collection_mean':{str(c):float(np.mean([r['difference_minus_zero'] for r in subset if r['collection_seed']==c])) for c in (4004,5005,6006)}})
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary['groups'],indent=2),flush=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,order in zip(axes,('ascending','descending')):
        for collection in (4004,5005,6006):
            vals=[np.mean([r['difference_minus_zero'] for r in contrasts if r['collection_seed']==collection and r['order']==order and r['recovery']==t]) for t in (0,64,256)]
            ax.plot([0,64,256],vals,'o-',label=f'data seed {collection}')
        ax.axhline(0,color='black',linewidth=.8);ax.set_title(order);ax.set_xlabel('Common clean recovery updates');ax.legend(fontsize=8)
    axes[0].set_ylabel('Extra order log-ratio: cumulative - frozen\nminus zero-amplitude control')
    fig.tight_layout();fig.savefig(OUT/'normalization_specific_contrast.png',dpi=160)

if __name__=='__main__':main()
