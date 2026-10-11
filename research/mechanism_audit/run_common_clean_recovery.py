"""Same clean tail and fresh Adam for every first-stage actor; frozen controls."""
import copy
import json
import math
import subprocess
import sys
from pathlib import Path
import torch
import run_full_width_order as p

ROOT=p.ROOT
SOURCE=ROOT/'full_width_order_pilot'
OUT=ROOT/'full_width_clean_recovery'
p.OUT=OUT
BRANCHES=('frozen','no_update','random','ascending','descending')


def validate_parent():
    result=json.loads((SOURCE/'results.json').read_text())
    summary=json.loads((SOURCE/'summary.json').read_text())
    assert result['complete'] and summary['complete'] and len(result['cases'])==40
    assert len({(r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees']) for r in result['cases']})==result['expected_cases_after_gates']==40
    assert sum(r['nan_count'] for r in result['cases'])==0
    assert sum(r['out_count'] for r in result['cases'])==0
    assert all(r['survival_count']==64 and len(r['rows'])==64 and r['state_unchanged'] for r in result['cases'])
    assert all(math.isfinite(row[k]) for r in result['cases'] for row in r['rows'] for k in ('seconds','return','mean_vx_error','mean_vy_error','mean_yaw_error','mean_action_delta'))
    assert all(g['baseline_valid'] for g in result['gates'])
    inventory=json.loads((SOURCE/'artifact_inventory.json').read_text())
    assert all(p.sha(SOURCE/r['file'])==r['sha256'] for r in inventory['files'])
    p.atomic_json(OUT/'parent_validation.json',{'complete':True,'cases':40,'episodes':2560,'nan_count':0,'out_count':0,'inventory_hashes_match':True,'source_results_sha256':p.sha(SOURCE/'results.json')})
    return result


def recover(teacher,branch):
    parentfile=SOURCE/f't{teacher}_{"no_update" if branch=="frozen" else branch}.pt'
    ledgerfile=ROOT/'normalization_confirmation'/f'ledger_t{teacher}_d7007_a6.json'
    datafile=ROOT/'normalization_confirmation'/f'teacher{teacher}'/'teacher_seed7007.pt'
    provenance={f'parent/{parentfile.name}':p.sha(parentfile),ledgerfile.name:p.sha(ledgerfile),datafile.name:p.sha(datafile)}
    target=OUT/f't{teacher}_{branch}.pt'
    if target.exists():
        saved=torch.load(target,map_location='cpu',weights_only=False)
        assert saved['complete'] and saved['provenance']==provenance
        return saved['summary']
    parent=torch.load(parentfile,map_location=p.D,weights_only=False)
    actor=copy.deepcopy(parent['actor']).to(p.D).eval()
    initial=p.snapshot(actor)
    ledger=json.loads(ledgerfile.read_text())
    assert ledger['data_sha256']==p.sha(datafile)
    ids=torch.tensor(ledger['sample_ids'],device=p.D)
    order=ledger['orders']['random']
    assert ids.shape==(256,192) and torch.unique(ids).numel()==49152 and sorted(order)==list(range(256))
    import hashlib
    schedule_hash=hashlib.sha256(ids[order].cpu().numpy().tobytes()).hexdigest()
    data=torch.load(datafile,map_location=p.D,weights_only=True)
    x=data['x'][:,:48].reshape(-1,61);y=data['y'][:,:48].reshape(-1,14)
    optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-5)
    step=0;loss=[]
    recovery=OUT/f't{teacher}_{branch}_progress.pt'
    if recovery.exists():
        saved=torch.load(recovery,map_location=p.D,weights_only=False)
        assert saved['provenance']==provenance
        actor=saved['actor'].to(p.D).eval();optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-5)
        optimizer.load_state_dict(saved['optimizer']);step=saved['step'];loss=saved['loss']
    if branch!='frozen':
        torch.use_deterministic_algorithms(True)
        for j in range(step,256):
            index=ids[order[j]]
            optimizer.zero_grad(set_to_none=True)
            objective=(p.infer(actor,x[index])-y[index]).square().mean()
            assert torch.isfinite(objective)
            objective.backward();optimizer.step();loss.append(float(objective.detach()))
            if (j+1)%64==0:
                tmp=recovery.with_suffix('.tmp')
                torch.save({'actor':actor,'optimizer':optimizer.state_dict(),'step':j+1,'loss':loss,'provenance':provenance},tmp)
                tmp.replace(recovery)
                print(f'RECOVERY teacher={teacher} parent={branch} step={j+1}',flush=True)
        torch.use_deterministic_algorithms(False)
    final=p.snapshot(actor)
    assert all(torch.equal(initial[k],final[k]) for k in initial if not k.startswith('mlp.'))
    assert all(torch.isfinite(v).all() for v in final.values())
    if branch=='frozen':assert all(torch.equal(initial[k],final[k]) for k in initial)
    summary={'teacher':teacher,'branch':branch,'steps':len(loss),'lr':1e-5,'loss':loss,'optimizer_reset':branch!='frozen',
             'clean_sample_schedule_sha256':schedule_hash,'immutable_state_unchanged':True,
             'max_weight_change':max(float((final[k]-initial[k]).abs().max()) for k in final if k.startswith('mlp.')),
             'offline_mse':p.offline(actor,teacher),'provenance':provenance}
    torch.save({'complete':True,'actor':actor.cpu(),'optimizer':optimizer.state_dict(),'summary':summary,'provenance':provenance,
                'warning':'Supervised clean-tail recovery only. Not native PPO or its resume checkpoint.'},target)
    return summary


def main():
    torch.set_num_threads(2);OUT.mkdir(exist_ok=True)
    validate_parent()
    path=OUT/'progress.json'
    result=json.loads(path.read_text()) if path.exists() else {'complete':False,'training':[],'cases':[],'gates':[]}
    def case(t,b,s,a):
        old=next((r for r in result['cases'] if (r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees'])==(t,b,s,a)),None)
        if old is not None:return old
        row=p.evaluate(t,b,s,a);result['cases'].append(row);p.atomic_json(path,result)
        print('RECOVERY_CASE '+json.dumps({k:v for k,v in row.items() if k!='rows'}),flush=True)
        return row
    for teacher in (42,2026):
        for branch in BRANCHES:
            if not any((r['teacher'],r['branch'])==(teacher,branch) for r in result['training']):
                result['training'].append(recover(teacher,branch));p.atomic_json(path,result)
        assert len({r['clean_sample_schedule_sha256'] for r in result['training'] if r['teacher']==teacher})==1
    for teacher in (42,2026):
        baseline=[case(teacher,'frozen',s,0) for s in p.EVAL_SEEDS]
        valid=all(r['survival_count']>=60 and r['nan_count']==0 and r['out_count']==0 for r in baseline)
        for branch in BRANCHES:
            nominal=[case(teacher,branch,s,0) for s in p.EVAL_SEEDS]
            passed=valid and all(r['survival_count']>=60 and r['mean_vx_error']<=base['mean_vx_error']+.02 and r['nan_count']==0 and r['out_count']==0 for r,base in zip(nominal,baseline))
            gate={'teacher':teacher,'branch':branch,'baseline_valid':valid,'nominal_gate_passed':passed}
            result['gates']=[r for r in result['gates'] if (r['teacher'],r['branch'])!=(teacher,branch)]+[gate]
            p.atomic_json(path,result)
        for gate in [r for r in result['gates'] if r['teacher']==teacher and r['nominal_gate_passed']]:
            for a in (-6,6):
                for s in p.EVAL_SEEDS:case(teacher,gate['branch'],s,a)
    expected=20+4*sum(g['nominal_gate_passed'] for g in result['gates'])
    assert len(result['cases'])==expected==len({(r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees']) for r in result['cases']})
    result['complete']=True;result['expected_cases_after_gates']=expected
    result['scope']='Matched 256-step clean supervised tail and fresh Adam; fixed original normalization. No native PPO or persistent-poisoning claim.'
    result['protocol_sha256']=p.sha(ROOT/'COMMON_CLEAN_RECOVERY_PROTOCOL.md')
    result['source_results_sha256']=p.sha(SOURCE/'results.json')
    p.atomic_json(path,result);p.atomic_json(OUT/'results.json',result)
    subprocess.run([sys.executable,str(ROOT/'analyze_common_clean_recovery.py')],check=True)
    print('RECOVERY_COMPLETE',flush=True)


if __name__=='__main__':main()
