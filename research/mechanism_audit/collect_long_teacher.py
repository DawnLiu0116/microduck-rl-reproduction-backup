"""Independent long simulation collections, with explicit episode boundaries."""
import hashlib
import argparse
import json
from dataclasses import asdict
from pathlib import Path

import torch
import mjlab.tasks
import mjlab_microduck.tasks
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg,load_rl_cfg,load_runner_cls
from rsl_rl.runners import OnPolicyRunner

OUT=Path(__file__).resolve().parent/'normalization_pilot'
CHECKPOINT=Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity/2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1/model_3999.pt')
RUNS={42:'2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2',123:'2026-09-22_19-08-01_walk_baseline_4096_seed123_4000_v1',2026:'2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--teacher-seed',type=int,choices=tuple(RUNS),default=123)
    parser.add_argument('--collection-seeds',type=int,nargs='+',default=[4004,5005,6006])
    parser.add_argument('--output-dir',type=Path,default=OUT)
    args=parser.parse_args()
    output=args.output_dir
    checkpoint=Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity')/RUNS[args.teacher_seed]/'model_3999.pt'
    teacher_hash=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    torch.set_num_threads(2)
    output.mkdir(parents=True,exist_ok=True)
    for seed in args.collection_seeds:
        path=output/f'teacher_seed{seed}.pt'
        if path.exists():
            saved=torch.load(path,map_location='cpu',weights_only=True)
            assert saved['x'].shape==(1024,64,61) and saved['done'].shape==(1024,64)
            assert saved['metadata']['teacher_sha256']==teacher_hash and saved['metadata']['collection_seed']==seed
            assert torch.isfinite(saved['x']).all() and torch.isfinite(saved['y']).all()
            print(f'EXISTING_VALID {path}',flush=True)
            continue
        task='Mjlab-Velocity-Flat-MicroDuck'
        cfg,agent=load_env_cfg(task,play=True),load_rl_cfg(task)
        cfg.scene.num_envs=64; cfg.seed=seed
        cfg.events['push_robot'].interval_range_s=(1000.,1001.)
        cfg.observations['actor'].enable_corruption=False
        for term in cfg.observations['actor'].terms.values():
            if 'max_angle_deg' in term.params:term.params['max_angle_deg']=0.
        # Retain task's mixed commands and native delays. Record exact inputs.
        env=RslRlVecEnvWrapper(ManagerBasedRlEnv(cfg=cfg,device='cuda:0'),clip_actions=agent.clip_actions)
        runner=(load_runner_cls(task) or OnPolicyRunner)(env,asdict(agent),device='cuda:0')
        runner.load(str(checkpoint),load_cfg={'actor':True},strict=True,map_location='cuda:0')
        policy=runner.get_inference_policy(device='cuda:0')
        obs=env.get_observations(); episode=torch.zeros(64,dtype=torch.long,device='cuda:0')
        xs,ys,ds,es=[],[],[],[]
        with torch.inference_mode():
            for step in range(1024):
                action=policy(obs)
                xs.append(obs['actor'].clone());ys.append(action.clone());es.append(episode.clone())
                obs,_,done,_=env.step(action)
                ds.append(done.bool().clone());episode+=done.long()
                if step%128==127:print(f'COLLECT seed={seed} step={step+1}/1024',flush=True)
        dt=float(env.unwrapped.step_dt)
        env.close()
        data={'x':torch.stack(xs).cpu(),'y':torch.stack(ys).cpu(),'done':torch.stack(ds).cpu(),'episode_id':torch.stack(es).cpu()}
        assert torch.isfinite(data['x']).all() and torch.isfinite(data['y']).all()
        assert torch.equal(data['episode_id'][1:],data['episode_id'][:-1]+data['done'][:-1].long())
        meta={'teacher_seed':args.teacher_seed,'collection_seed':seed,'steps':1024,'num_envs':64,'step_dt':dt,'seconds_per_env':1024*dt,'teacher_sha256':teacher_hash,'teacher_checkpoint':str(checkpoint),'task':task,'play_cfg':True,'noise_enabled':False,'imu_mount_angle_deg':0.,'push_interval_s':[1000,1001],'commands':'task mixed commands, stored at x[48:61]','native_observation_delay_retained':True,'split':'env 0:48 train, 48:64 test','termination_transitions':int(data['done'].sum()),'finite':True}
        data['metadata']=meta
        tmp=path.with_suffix('.tmp');torch.save(data,tmp);tmp.replace(path)
        (output/f'teacher_seed{seed}_metadata.json').write_text(json.dumps(meta,indent=2))
        print(json.dumps(meta),flush=True)

if __name__=='__main__':main()
