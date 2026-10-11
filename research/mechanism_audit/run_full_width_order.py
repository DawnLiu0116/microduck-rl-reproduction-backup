"""Bounded, resumable full-width warm-start supervised order pilot and real simulation."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import copy
import json
import time
import importlib.metadata
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
import mjlab.tasks
import mjlab_microduck.tasks
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
from run_normalization_pilot import rotate
from verify_ppo_clone import sha, atomic_json, snapshot

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_order_pilot'
D='cuda:0'
TASK='Mjlab-Velocity-Flat-MicroDuck'
BRANCHES=('no_update','random','ascending','descending')
EVAL_SEEDS=(11011,12012)


def infer(actor,x):
    return actor(TensorDict({'actor':x},batch_size=[len(x)]))


def offline(actor,teacher):
    result={}
    with torch.inference_mode():
        for seed in (9009,10010):
            data=torch.load(ROOT/'replay_fork_pilot'/f'eval_teacher{teacher}'/f'teacher_seed{seed}.pt',map_location=D,weights_only=True)
            x=data['x'].reshape(-1,61);y=data['y'].reshape(-1,14)
            result[str(seed)]={}
            for a in (0,-6,6):
                total=0.
                for start in range(0,len(x),1024):
                    prediction=infer(actor,rotate(x[start:start+1024],a))
                    assert torch.isfinite(prediction).all()
                    total+=float((prediction-y[start:start+1024]).square().sum())
                result[str(seed)][str(a)]=total/(len(x)*14)
    return result


def train(teacher,branch):
    startfile=ROOT/'ppo_clone_baseline'/f'seed{teacher}_serialized_actor.pt'
    datafile=ROOT/'normalization_confirmation'/f'teacher{teacher}'/'teacher_seed7007.pt'
    ledgerfile=ROOT/'normalization_confirmation'/f'ledger_t{teacher}_d7007_a6.json'
    path=OUT/f't{teacher}_{branch}.pt'
    initial=torch.load(startfile,map_location=D,weights_only=False).eval()
    initial_state=snapshot(initial)
    provenance={p.name:sha(p) for p in (startfile,datafile,ledgerfile)}
    if path.exists():
        saved=torch.load(path,map_location='cpu',weights_only=False)
        assert saved['provenance']==provenance and saved['complete']
        return saved['summary']
    ledger=json.loads(ledgerfile.read_text())
    assert ledger['data_sha256']==provenance[datafile.name]
    ids=torch.tensor(ledger['sample_ids'],device=D)
    assert ids.shape==(256,192) and torch.unique(ids).numel()==49152
    for order in ledger['orders'].values():assert sorted(order)==list(range(256))
    assert max(abs(a) for a in ledger['angles'])==6
    data=torch.load(datafile,map_location=D,weights_only=True)
    x=data['x'][:,:48].reshape(-1,61);y=data['y'][:,:48].reshape(-1,14)
    assert x.shape==(49152,61) and y.shape==(49152,14)
    actor=copy.deepcopy(initial)
    optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-5)
    recovery=OUT/f't{teacher}_{branch}_progress.pt'
    loss=[];step=0
    if recovery.exists():
        saved=torch.load(recovery,map_location=D,weights_only=False)
        assert saved['provenance']==provenance
        actor=saved['actor'].to(D).eval();optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-5)
        optimizer.load_state_dict(saved['optimizer']);step=saved['step'];loss=saved['loss']
    if branch!='no_update':
        torch.use_deterministic_algorithms(True)
        order=ledger['orders'][branch]
        for j in range(step,256):
            index=order[j];batch=rotate(x[ids[index]],ledger['angles'][index])
            optimizer.zero_grad(set_to_none=True)
            objective=(infer(actor,batch)-y[ids[index]]).square().mean()
            assert torch.isfinite(objective)
            objective.backward();optimizer.step();loss.append(float(objective))
            if (j+1)%64==0:
                temp=recovery.with_suffix('.tmp')
                torch.save({'actor':actor,'optimizer':optimizer.state_dict(),'step':j+1,'loss':loss,'provenance':provenance},temp)
                temp.replace(recovery)
                print(f'TRAIN teacher={teacher} branch={branch} step={j+1} loss={loss[-1]:.6g}',flush=True)
        torch.use_deterministic_algorithms(False)
    final=snapshot(actor)
    immutable=[k for k in initial_state if not k.startswith('mlp.')]
    assert all(torch.equal(initial_state[k],final[k]) for k in immutable)
    assert all(torch.isfinite(v).all() for v in final.values())
    if branch=='no_update':assert all(torch.equal(initial_state[k],final[k]) for k in initial_state)
    summary={'teacher':teacher,'branch':branch,'steps':len(loss),'lr':1e-5,
             'max_weight_change':max(float((final[k]-initial_state[k]).abs().max()) for k in final if k.startswith('mlp.')),
             'immutable_state_unchanged':True,'offline_mse':offline(actor,teacher),'loss':loss,
             'provenance':provenance,'actor_file':path.name}
    torch.save({'complete':True,'actor':actor.cpu(),'optimizer':optimizer.state_dict(),'summary':summary,'provenance':provenance,
                'warning':'Supervised actor only. Not a PPO resume checkpoint.'},path)
    return summary


def evaluate(teacher,branch,seed,angle):
    actor=torch.load(OUT/f't{teacher}_{branch}.pt',map_location=D,weights_only=False)['actor'].eval()
    before=snapshot(actor)
    cfg,agent=load_env_cfg(TASK,play=True),load_rl_cfg(TASK)
    cfg.scene.num_envs=64;cfg.seed=seed;cfg.episode_length_s=20.;cfg.curriculum={}
    cfg.events['push_robot'].interval_range_s=(1000.,1001.)
    cfg.observations['actor'].enable_corruption=False
    for term in cfg.observations['actor'].terms.values():
        if 'max_angle_deg' in term.params:term.params['max_angle_deg']=0.
    twist=cfg.commands['twist']
    twist.ranges.lin_vel_x=(.3,.3);twist.ranges.lin_vel_y=(0.,0.);twist.ranges.ang_vel_z=(0.,0.)
    twist.resampling_time_range=(1000.,1001.)
    for attr in ('rel_standing_envs','rel_forward_envs','rel_turn_in_place_envs','rel_heading_envs'):setattr(twist,attr,0.)
    for name in ('head_pose','body_pose'):
        term=cfg.commands[name];term.ranges=tuple((0.,0.) for _ in term.ranges)
        term.resampling_time_range=(1000.,1001.);term.zero_command_prob=1.
    env=None
    try:
        base=ManagerBasedRlEnv(cfg=cfg,device=D)
        env=RslRlVecEnvWrapper(base,clip_actions=agent.clip_actions)
        # Match the native runner's restored environment counter without changing curricula.
        checkpoint=torch.load(ROOT/'ppo_clone_baseline'/f'seed{teacher}_clone_model3999.pt',map_location='cpu',weights_only=False)
        info=checkpoint.get('infos') or {}
        if 'env_state' in info:base.common_step_counter=info['env_state']['common_step_counter']
        obs=env.get_observations()
        initial_sha=__import__('hashlib').sha256(obs['actor'].cpu().numpy().tobytes()).hexdigest()
        active=torch.ones(64,dtype=torch.bool,device=D);steps=torch.zeros(64,dtype=torch.long,device=D)
        totals={k:torch.zeros(64,device=D) for k in ('return','vx_error','vy_error','yaw_error','action_delta')}
        causes={k:torch.zeros(64,dtype=torch.bool,device=D) for k in ('fell_over','time_out','nan_state','out_of_terrain_bounds')}
        previous=None;max_action=0.
        with torch.inference_mode():
            for frame in range(1100):
                if not bool(active.any()):break
                command=base.command_manager.get_term('twist').vel_command_b
                assert float((command-torch.tensor([.3,0.,0.],device=D)).abs().max())<1e-6
                vel=base.scene['robot'].data.root_link_lin_vel_b
                yaw=base.scene['robot'].data.root_link_ang_vel_b[:,2]
                assert torch.isfinite(vel[active]).all() and torch.isfinite(yaw[active]).all()
                totals['vx_error']+=(vel[:,0]-.3).abs()*active
                totals['vy_error']+=vel[:,1].abs()*active;totals['yaw_error']+=yaw.abs()*active
                action=infer(actor,rotate(obs['actor'],angle))
                assert action.shape==(64,14) and torch.isfinite(action).all()
                max_action=max(max_action,float(action[active].abs().max()))
                if previous is not None:totals['action_delta']+=(action-previous).abs().mean(1)*active
                previous=action.clone()
                obs,reward,done,_=env.step(action)
                assert torch.isfinite(reward[active]).all()
                totals['return']+=reward*active;steps+=active.long()
                ended=done.bool()&active
                for name in causes:causes[name]|=ended&base.termination_manager.get_term(name)
                active&=~ended
        assert not bool(active.any())
        final=snapshot(actor);assert all(torch.equal(v,final[k]) for k,v in before.items())
        survive=causes['time_out']&~causes['fell_over']&~causes['nan_state']&~causes['out_of_terrain_bounds']
        rows=[{'env_id':i,'steps':int(steps[i]),'seconds':float(steps[i])*base.step_dt,'survival':bool(survive[i]),
               **{k:bool(v[i]) for k,v in causes.items()},'return':float(totals['return'][i]),
               **{f'mean_{k}':float(v[i]/steps[i]) for k,v in totals.items() if k!='return'}} for i in range(64)]
        return {'teacher':teacher,'branch':branch,'eval_seed':seed,'pitch_degrees':angle,'survival_count':int(survive.sum()),
                'nan_count':int(causes['nan_state'].sum()),'out_count':int(causes['out_of_terrain_bounds'].sum()),
                'mean_vx_error':float(np.mean([r['mean_vx_error'] for r in rows])),
                'mean_episode_seconds':float(np.mean([r['seconds'] for r in rows])),
                'initial_obs_sha256':initial_sha,'max_abs_action':max_action,'state_unchanged':True,'rows':rows}
    finally:
        if env is not None:env.close()


def main():
    torch.set_num_threads(2)
    OUT.mkdir(exist_ok=True)
    path=OUT/'progress.json'
    result=json.loads(path.read_text()) if path.exists() else {'complete':False,'training':[],'cases':[],'gates':[]}
    def run_case(t,b,s,a):
        for r in result['cases']:
            if (r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees'])==(t,b,s,a):return r
        row=evaluate(t,b,s,a);result['cases'].append(row);atomic_json(path,result)
        print('SIM_CASE '+json.dumps({k:v for k,v in row.items() if k!='rows'}),flush=True)
        return row
    for teacher in (42,2026):
        for branch in BRANCHES:
            if not any(r['teacher']==teacher and r['branch']==branch for r in result['training']):
                row=train(teacher,branch);result['training'].append(row);atomic_json(path,result)
    for teacher in (42,2026):
        baseline=[run_case(teacher,'no_update',s,0) for s in EVAL_SEEDS]
        baseline_ok=all(r['survival_count']>=60 and r['nan_count']==0 and r['out_count']==0 for r in baseline)
        for branch in BRANCHES:
            nominal=[run_case(teacher,branch,s,0) for s in EVAL_SEEDS]
            passed=baseline_ok and all(r['survival_count']>=60 and r['nan_count']==0 and r['out_count']==0 and r['mean_vx_error']<=base['mean_vx_error']+.02 for r,base in zip(nominal,baseline))
            gate={'teacher':teacher,'branch':branch,'baseline_valid':baseline_ok,'nominal_gate_passed':passed}
            result['gates']=[r for r in result['gates'] if (r['teacher'],r['branch'])!=(teacher,branch)]+[gate]
            atomic_json(path,result)
        # Nominal gates are decided before running any fault for this source model.
        for gate in [r for r in result['gates'] if r['teacher']==teacher and r['nominal_gate_passed']]:
            for angle in (-6,6):
                for seed in EVAL_SEEDS:run_case(teacher,gate['branch'],seed,angle)
    assert len(result['training'])==8 and len(result['gates'])==8
    expected=16+4*sum(r['nominal_gate_passed'] for r in result['gates'])
    assert len(result['cases'])==expected
    assert len({(r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees']) for r in result['cases']})==expected
    result['complete']=True;result['expected_cases_after_gates']=expected
    result['scope']='Full-width PPO actor supervised warm-start; frozen original normalization; fixed multiset, different order. Not native PPO training or proof of poisoning.'
    result['provenance']={'commit':subprocess.check_output(['git','-C','/home/deuler/microduck_rl','rev-parse','HEAD'],text=True).strip(),
                          'versions':{n:importlib.metadata.version(n) for n in ('torch','mjlab','rsl-rl-lib','mujoco','warp-lang')},
                          'scripts_sha256':{n:sha(ROOT/n) for n in ('run_full_width_order.py','analyze_full_width_order.py','FULL_WIDTH_ORDER_PROTOCOL.md')}}
    atomic_json(path,result);atomic_json(OUT/'results.json',result)
    print('PILOT_COMPLETE '+json.dumps({'cases':expected,'episodes':expected*64,'gates':result['gates']}),flush=True)
    subprocess.run([sys.executable,str(ROOT/'analyze_full_width_order.py')],check=True)


if __name__=='__main__':main()
