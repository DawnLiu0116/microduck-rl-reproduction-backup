"""Record pre-reset raw state from official mjlab; first episodes only."""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import torch
from collect_long_teacher import RUNS
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import RslRlVecEnvWrapper
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
from rsl_rl.runners import OnPolicyRunner

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'sim_fall_filter'
TASK = 'Mjlab-Velocity-Flat-MicroDuck'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect(model, seed, scenario, smoke=False):
    out = OUT/f'm{model}_s{seed}_{scenario}{"_smoke" if smoke else ""}.pt'
    checkpoint = Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity')/RUNS[model]/'model_3999.pt'
    if out.exists():
        old = torch.load(out, weights_only=True)
        assert old['metadata']['complete'] and old['metadata']['checkpoint_sha256'] == sha(checkpoint)
        print('VALID_EXISTING '+out.name, flush=True)
        return
    cfg, agent = load_env_cfg(TASK, play=True), load_rl_cfg(TASK)
    cfg.scene.num_envs = 4 if smoke else 16
    cfg.seed = seed; cfg.episode_length_s = 10.; cfg.curriculum = {}
    cfg.events['push_robot'].interval_range_s = (1000.,1001.) if scenario == 'Nominal' else (.5,1.)
    cfg.observations['actor'].enable_corruption = False
    for term in cfg.observations['actor'].terms.values():
        if 'max_angle_deg' in term.params: term.params['max_angle_deg'] = 0.
    twist = cfg.commands['twist']
    twist.ranges.lin_vel_x=(.3,.3); twist.ranges.lin_vel_y=(0.,0.); twist.ranges.ang_vel_z=(0.,0.)
    twist.resampling_time_range=(1000.,1001.)
    for name in ('rel_standing_envs','rel_forward_envs','rel_turn_in_place_envs','rel_heading_envs'):
        setattr(twist,name,0.)
    for name in ('head_pose','body_pose'):
        term=cfg.commands[name];term.ranges=tuple((0.,0.) for _ in term.ranges)
        term.resampling_time_range=(1000.,1001.);term.zero_command_prob=1.
    base=ManagerBasedRlEnv(cfg=cfg,device='cuda:0')
    env=RslRlVecEnvWrapper(base,clip_actions=agent.clip_actions)
    try:
        runner=(load_runner_cls(TASK) or OnPolicyRunner)(env,asdict(agent),device='cuda:0')
        runner.load(str(checkpoint),load_cfg={'actor':True},strict=True,map_location='cuda:0')
        policy=runner.get_inference_policy(device='cuda:0')
        obs=env.get_observations()
        original=base.termination_manager.compute
        captured={}
        causes=list(cfg.terminations)
        def hooked_compute(*args,**kwargs):
            result=original(*args,**kwargs)
            robot=base.scene['robot'].data
            contact=base.scene.sensors['feet_ground_contact'].data
            for key,value in {'gyro':robot.root_link_ang_vel_b,'gravity':robot.projected_gravity_b,
                              'quat':robot.root_link_quat_w,'position':robot.root_link_pos_w,
                              'contact_found':contact.found,'contact_force':contact.force,
                              'done':result}.items():
                captured[key]=value.detach().clone()
            for name in causes:captured['term_'+name]=base.termination_manager.get_term(name).detach().clone()
            return result
        base.termination_manager.compute=hooked_compute
        active=torch.ones(base.num_envs,dtype=torch.bool,device='cuda:0')
        traces={}
        with torch.inference_mode():
            for frame in range(5 if smoke else 510):
                if not active.any():break
                command=base.command_manager.get_term('twist').vel_command_b
                assert (command-torch.tensor([.3,0,0],device='cuda:0')).abs().max()<1e-6
                action=policy(obs)
                assert torch.isfinite(action).all()
                before_active=active.clone()
                obs, reward, done, _=env.step(action)
                assert torch.equal(done.bool(),captured['done'].bool())
                row={**captured,'active':before_active,'action':action.detach().clone()}
                for key,value in row.items():
                    assert torch.isfinite(value).all(),key
                    traces.setdefault(key,[]).append(value.cpu())
                active &= ~done.bool()
                if frame%100==99:print(f'STEP {out.name} {frame+1} active={int(active.sum())}',flush=True)
        assert smoke or not active.any()
        metadata={'complete':True,'model':model,'seed':seed,'scenario':scenario,'smoke':smoke,
                  'num_envs':base.num_envs,'dt':float(base.step_dt),'frames':len(traces['active']),
                  'checkpoint_sha256':sha(checkpoint),'protocol_sha256':sha(ROOT/'SIM_FALL_FILTER_PROTOCOL.md'),
                  'push_params':str(cfg.events['push_robot'].params),
                  'sample_phase':'termination compute, pre-reset, derived state may lag one physics substep',
                  'script_sha256':sha(Path(__file__))}
        data={k:torch.stack(v) for k,v in traces.items()}; data['metadata']=metadata
        tmp=out.with_suffix('.tmp');torch.save(data,tmp);tmp.replace(out)
        print('SAVED '+json.dumps(metadata),flush=True)
    finally:
        env.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    torch.set_num_threads(2); OUT.mkdir(exist_ok=True)
    if args.smoke:collect(42,11011,'Nominal',True)
    else:
        for model in (42,123,2026):
            for seed in (11011,12012):
                for scenario in ('Nominal','Stress'):collect(model,seed,scenario)


if __name__=='__main__':main()
