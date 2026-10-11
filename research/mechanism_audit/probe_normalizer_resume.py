"""Redundant normalization-state contract, only in-memory CPU diagnostics."""
import copy
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import numpy as np
import torch
from rsl_rl.modules import EmpiricalNormalization

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'normalizer_resume_probe'
RUNS={42:'2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2',
      123:'2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1',
      2026:'2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(state):
    finite=all(torch.isfinite(v).all().item() for v in state.values())
    nonnegative=bool((state['_var']>=0).all() and (state['_std']>=0).all())
    residual=float((state['_std']-torch.sqrt(state['_var'])).abs().max()) if nonnegative else None
    count=state['count']
    valid_count=count.numel()==1 and count.dtype==torch.long and int(count)>=0
    coherent=nonnegative and torch.allclose(state['_std'],torch.sqrt(state['_var']),atol=1e-7,rtol=1e-6)
    return {'finite':finite,'nonnegative':nonnegative,'valid_count':bool(valid_count),
            'std_sqrtvar_max_abs_error':residual,'coherent':bool(coherent),
            'contract_passed':bool(finite and nonnegative and valid_count and coherent),'count':int(count)}


def infer(state,norm,x):
    z=norm(x)
    for layer in (0,2,4):
        z=torch.nn.functional.elu(torch.nn.functional.linear(z,state[f'mlp.{layer}.weight'],state[f'mlp.{layer}.bias']))
    return torch.nn.functional.linear(z,state['mlp.6.weight'],state['mlp.6.bias'])


def diff(a,b):
    d=(a-b).abs()
    return {'mean_abs':float(d.mean()),'max_abs':float(d.max()),
            'mean_action_l2':float(torch.linalg.vector_norm(a-b,dim=1).mean()),
            'exact_equal':bool(torch.equal(a,b))}


def main():
    torch.set_num_threads(2);OUT.mkdir(exist_ok=True)
    data_path=ROOT/'normalization_confirmation/teacher42/teacher_seed7007.pt'
    data=torch.load(data_path,map_location='cpu',weights_only=True)
    update_batch=data['x'][:16,:16].reshape(256,61).clone()
    heldout=data['x'][:,48:64].reshape(-1,61)[::8].clone()
    assert heldout.shape==(2048,61)
    rows=[]
    for seed,run in RUNS.items():
        path=Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity')/run/'model_3999.pt'
        original_sha=sha(path)
        actor=torch.load(path,map_location='cpu',weights_only=False)['actor_state_dict']
        original={k.removeprefix('obs_normalizer.'):v.clone() for k,v in actor.items() if k.startswith('obs_normalizer.')}
        assert validate(original)['contract_passed']
        clean=EmpiricalNormalization(61).eval();clean.load_state_dict(original,strict=True)
        with torch.inference_mode():clean_y=infer(actor,clean,heldout)
        outputs={}
        for branch in ('original','var_only_1pct','coherent_1pct','count_zero'):
            state=copy.deepcopy(original)
            if branch in ('var_only_1pct','coherent_1pct'):state['_var']*=1.01
            if branch=='coherent_1pct':state['_std']=torch.sqrt(state['_var'])
            if branch=='count_zero':state['count'].zero_()
            norm=EmpiricalNormalization(61).eval()
            norm.load_state_dict(state,strict=True)
            pre=validate(norm.state_dict())
            with torch.inference_mode():before=infer(actor,norm,heldout)
            saved=copy.deepcopy(norm.state_dict());norm.update(update_batch)
            assert all(torch.equal(v,norm.state_dict()[k]) for k,v in saved.items())
            norm.train();norm.update(update_batch);norm.eval()
            post=validate(norm.state_dict())
            with torch.inference_mode():after=infer(actor,norm,heldout)
            assert torch.isfinite(before).all() and torch.isfinite(after).all()
            outputs[branch]=(before,after)
            rows.append({'seed':seed,'branch':branch,'strict_load_accepted':True,'pre_contract':pre,
                         'eval_update_unchanged':True,'post_contract':post,
                         'pre_vs_original':diff(before,clean_y),
                         'post_vs_own_pre':diff(after,before),
                         'checkpoint_sha256':original_sha})
        for row in (r for r in rows if r['seed']==seed):
            row['post_vs_original_post']=diff(outputs[row['branch']][1],outputs['original'][1])
        assert torch.equal(outputs['var_only_1pct'][0],clean_y)
        assert not torch.equal(outputs['var_only_1pct'][1],outputs['original'][1])
        assert sha(path)==original_sha
    result={'complete':True,'rows':rows,'eval_frames_per_model':2048,'update_batch_frames':256,
            'dataset_sha256':sha(data_path),'original_models_unchanged':True,
            'normalizer_source_sha256':sha(Path(inspect.getfile(EmpiricalNormalization))),
            'script_sha256':sha(Path(__file__)),'protocol_sha256':sha(ROOT/'NORMALIZER_RESUME_PROTOCOL.md'),
            'versions':{p:importlib.metadata.version(p) for p in ('torch','rsl-rl-lib','numpy')},
            'scope':'In-memory buffer consistency and single explicit normalization update; no optimizer or PPO update.',
            'limits':['All models evaluated on one existing teacher42 dataset.',
                      'Clean/fault closed-loop effects not tested.',
                      'A mismatched buffer is an artificial fault, not evidence of existing model compromise.',
                      'Passing the coherence check does not establish state authenticity or representativeness.',
                      'eps/until are external attributes and need a separate saved configuration contract.']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
