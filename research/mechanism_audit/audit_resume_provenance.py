"""Read-only audit of real checkpoints, configs, events, and exported normalizers."""
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import numpy as np
import onnx
from onnx import numpy_helper
import torch
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from rsl_rl.modules import EmpiricalNormalization

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'resume_provenance_audit'
REPO=Path('/home/deuler/microduck_rl')
BASE=REPO/'logs/rsl_rl/velocity'
RUNS={
 'seed42':'2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2',
 'seed123':'2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1',
 'seed2026_parent':'2026-09-28_20-54-07_walk_baseline_4096_seed2026_4000_v1',
 'seed2026_resume':'2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet'}


class ConfigLoader(yaml.SafeLoader):pass
ConfigLoader.add_constructor('tag:yaml.org,2002:python/tuple',lambda loader,node:loader.construct_sequence(node))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalizer(state):
    s={k.removeprefix('obs_normalizer.'):v for k,v in state.items() if k.startswith('obs_normalizer.')}
    assert set(s)=={'_mean','_var','_std','count'}
    finite=all(torch.isfinite(v).all().item() for v in s.values())
    assert finite and (s['_var']>=0).all() and (s['_std']>=0).all()
    error=float((torch.sqrt(s['_var'])-s['_std']).abs().max())
    assert error<1e-7
    return {'count':int(s['count']),'coherence_max_abs_error':error,'finite':finite,
            'shape':list(s['_mean'].shape)}


def events(run):
    summaries=[]
    for p in sorted(run.glob('events.out.tfevents.*')):
        acc=EventAccumulator(str(p),size_guidance={'scalars':0});acc.Reload()
        tags=acc.Tags()['scalars']
        chosen=next((t for t in tags if t.lower() in ('train/mean_reward','train/mean_reward/time')),None)
        if chosen is None:chosen=next((t for t in tags if 'mean_reward' in t.lower()),tags[0] if tags else None)
        samples=acc.Scalars(chosen) if chosen else []
        steps=[v.step for v in samples]
        summaries.append({'file':p.name,'sha256':sha(p),'tag':chosen,'entries':len(steps),
                          'first_step':min(steps) if steps else None,'last_step':max(steps) if steps else None,
                          'unique_steps':len(set(steps))})
    return summaries


def main():
    torch.set_num_threads(2);OUT.mkdir(exist_ok=True)
    runs={};all_rows=[]
    for label,name in RUNS.items():
        run=BASE/name
        agent_path=run/'params/agent.yaml';env_path=run/'params/env.yaml'
        cfg=yaml.load(agent_path.read_text(),Loader=ConfigLoader)
        files=sorted(run.glob('model_*.pt'),key=lambda p:int(p.stem.split('_')[1]))
        rows=[]
        for p in files:
            cp=torch.load(p,map_location='cpu',weights_only=False)
            actor=normalizer(cp['actor_state_dict']);critic=normalizer(cp['critic_state_dict'])
            iteration=int(cp['iter']);counter=int(cp['infos']['env_state']['common_step_counter'])
            optimizer=cp['optimizer_state_dict']
            steps=[int(s['step']) for s in optimizer['state'].values() if 'step' in s]
            row={'run':label,'file':p.name,'iter':iteration,'env_counter':counter,'actor':actor,'critic':critic,
                 'optimizer_step_min':min(steps) if steps else None,'optimizer_step_max':max(steps) if steps else None,
                 'sha256':sha(p),'rollouts_from_actor_count':actor['count']/98304,
                 'offset_rollouts_vs_iteration':actor['count']/98304-(iteration+1)}
            assert actor['count']==critic['count']==counter*4096
            assert actor['count']%98304==0 and counter%24==0
            assert iteration==int(p.stem.split('_')[1])
            rows.append(row)
        for a,b in zip(rows,rows[1:]):
            assert b['actor']['count']-a['actor']['count']==(b['iter']-a['iter'])*98304
            assert b['env_counter']-a['env_counter']==(b['iter']-a['iter'])*24
        runs[label]={'directory':str(run),'checkpoint_count':len(rows),'checkpoints':rows,
                     'config':{k:cfg[k] for k in ('seed','num_steps_per_env','max_iterations','resume','load_run','load_checkpoint','actor','critic','algorithm')},
                     'agent_yaml_sha256':sha(agent_path),'env_yaml_sha256':sha(env_path),
                     'events':events(run)}
        all_rows.extend(rows)
        print(f'AUDITED {label}: {len(rows)} checkpoints',flush=True)
    parent=next(r for r in runs['seed2026_parent']['checkpoints'] if r['iter']==3250)
    resume=runs['seed2026_resume']['checkpoints'][0]
    assert resume['iter']==3250 and resume['actor']['count']-parent['actor']['count']==98304
    assert resume['env_counter']-parent['env_counter']==24
    assert runs['seed2026_resume']['config']['load_run']==RUNS['seed2026_parent']
    assert runs['seed2026_resume']['config']['load_checkpoint']=='model_3250.pt'
    # Configuration differences other than resume bookkeeping are reported, not suppressed.
    config_diff={k:{'parent':runs['seed2026_parent']['config'][k],'resume':runs['seed2026_resume']['config'][k]}
                 for k in runs['seed2026_parent']['config'] if runs['seed2026_parent']['config'][k]!=runs['seed2026_resume']['config'][k]}
    exports=[]
    for seed,label in ((42,'seed42'),(123,'seed123'),(2026,'seed2026_resume')):
        p=BASE/RUNS[label]/'model_3999.pt'
        state=torch.load(p,map_location='cpu',weights_only=False)['actor_state_dict']
        model=ROOT.parent/f'microduck_velocity_flat_seed{seed}_iter3999.onnx'
        graph=onnx.load(str(model));onnx.checker.check_model(graph)
        initial={v.name:numpy_helper.to_array(v) for v in graph.graph.initializer}
        for node in graph.graph.node:
            if node.op_type=='Constant' and node.attribute and node.attribute[0].type==onnx.AttributeProto.TENSOR:
                initial[node.output[0]]=numpy_helper.to_array(node.attribute[0].t)
        sub=next(n for n in graph.graph.node if n.op_type=='Sub' and n.input[0]==graph.graph.input[0].name)
        div=next(n for n in graph.graph.node if n.op_type=='Div' and n.input[0]==sub.output[0])
        mean=initial[sub.input[1]];denominator=initial[div.input[1]]
        mean_error=float(np.abs(mean-state['obs_normalizer._mean'].numpy()).max())
        denominator_error=float(np.abs(denominator-(state['obs_normalizer._std']+.01).numpy()).max())
        assert mean_error<1e-7 and denominator_error<1e-7
        copied=ROOT.parent/('checkpoints/model_3999.pt' if seed==42 else f'checkpoints/microduck_velocity_flat_seed{seed}_iter3999.pt')
        copy_exists=copied.exists()
        if copy_exists:assert sha(copied)==sha(p)
        exports.append({'seed':seed,'onnx_sha256':sha(model),
                        'checkpoint_copy_expected_path':str(copied),'checkpoint_copy_exists':copy_exists,
                        'checkpoint_copy_matches':True if copy_exists else None,
                        'mean_max_abs_error':mean_error,'denominator_max_abs_error':denominator_error,
                        'eps_source':'Current installed default=0.01; graph checked against std+0.01, not historical attribute serialization'})
    result={'complete':True,'checkpoint_count':len(all_rows),'runs':runs,'resume_config_differences':config_diff,
            'parent_resume_boundary':{'parent':parent,'first_resume':resume,
                'count_delta':resume['actor']['count']-parent['actor']['count'],
                'env_counter_delta':resume['env_counter']-parent['env_counter'],
                'optimizer_step_delta':resume['optimizer_step_min']-parent['optimizer_step_min']},
            'exports':exports,'versions':{p:importlib.metadata.version(p) for p in ('torch','rsl-rl-lib','mjlab','onnx')},
            'source_sha256':{str(p):sha(p) for p in (Path(inspect.getfile(EmpiricalNormalization)),
                REPO/'.venv/lib/python3.12/site-packages/rsl_rl/runners/on_policy_runner.py',
                REPO/'.venv/lib/python3.12/site-packages/mjlab/rl/runner.py')},
            'commit':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
            'limits':['Only saved checkpoints audited; discarded steps after last parent checkpoint are not part of restored lineage.',
                'Checkpoint does not capture full live simulator/RNG state; resume is not bitwise uninterrupted training.',
                'No historical source-version lock for ordinary eps/until attributes; matching exported denominator is verified.',
                'Current code and saved configs explain counters; no malicious alteration or actual robustness change established.']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'complete':True,'checkpoint_count':len(all_rows),'boundary':result['parent_resume_boundary'],'config_diff_keys':list(config_diff),'exports':exports},indent=2))


if __name__=='__main__':main()
