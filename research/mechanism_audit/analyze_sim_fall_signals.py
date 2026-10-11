"""Offline paired detector comparison on first-episode physics traces."""
import hashlib
import json
import subprocess
import importlib.metadata
from pathlib import Path
import numpy as np
import torch
from collect_long_teacher import load_env_cfg
from probe_fall_filter import predictor, delay, median
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sim_fall_filter'


def main():
    torch.set_num_threads(2)
    rows=[]; cases=[]
    for model in (42,123,2026):
        for seed in (11011,12012):
            for scenario in ('Nominal','Stress'):
                path=OUT/f'm{model}_s{seed}_{scenario}.pt'
                data=torch.load(path,map_location='cpu',weights_only=True)
                meta=data['metadata'];assert meta['complete'] and meta['num_envs']==16 and abs(meta['dt']-.02)<1e-8
                assert all(torch.isfinite(v).all() for v in data.values() if isinstance(v,torch.Tensor))
                for env in range(16):
                    valid=data['active'][:,env].numpy()
                    n=int(valid.sum());assert valid[:n].all() and not valid[n:].any()
                    assert bool(data['done'][n-1,env])
                    g=data['gravity'][:n,env].numpy();w=data['gyro'][:n,env].numpy()
                    q=data['quat'][:n,env].numpy()
                    qw,qx,qy,qz=q.T
                    expected_g=np.column_stack([2*(qw*qy-qx*qz),-2*(qw*qx+qy*qz),-1+2*(qx*qx+qy*qy)])
                    quat_gravity_error=float(np.abs(expected_g-g).max())
                    assert quat_gravity_error < 1e-4, 'Quaternion/gravity convention mismatch'
                    gd=delay(g,[0,0,-1]);wd=delay(w,[0,0,0])
                    gm=median(g,[0,0,-1]);wm=median(w,[0,0,0])
                    branches={'raw':(g,w),'delay1':(gd,wd),'median3':(gm,wm),
                              'median3_unit':(gm/np.linalg.norm(gm,axis=1)[:,None],wm),
                              'gyro_delay1':(g,wd),'gravity_delay1':(gd,w)}
                    causes={key[5:]:bool(value[n-1,env]) for key,value in data.items() if key.startswith('term_')}
                    crossed=np.flatnonzero(g[:,2]>-.5)
                    cross=float((crossed[0]+1)*.02) if len(crossed) else None
                    found=data['contact_found'][:n,env].numpy().reshape(n,-1)
                    force=data['contact_force'][:n,env].numpy()
                    episode={'model':model,'seed':seed,'scenario':scenario,'env':env,'frames':n,
                             'duration_s':n*.02,'termination':causes,'cross_60deg_s':cross,
                             'max_tilt_deg':float(np.rad2deg(np.arccos(np.clip(-g[:,2],-1,1))).max()),
                             'quat_gravity_max_abs_error':quat_gravity_error,
                             'no_foot_contact_frames':int((~found.astype(bool).any(axis=1)).sum()),
                             'max_abs_contact_force_N':float(np.abs(force).max()),
                             'branches':{}}
                    for branch,(bg,bw) in branches.items():
                        rate,pred,events=predictor(bg,bw)
                        times=[(i+1)*.02 for i in events]
                        episode['branches'][branch]={'trigger_times_s':times,
                            'first_trigger_s':times[0] if times else None,
                            'lead_to_60deg_s':None if cross is None or not times else cross-times[0]}
                    episode['median_vs_delay_all_events_equal']=episode['branches']['median3']['trigger_times_s']==episode['branches']['delay1']['trigger_times_s']
                    episode['median_vs_delay_first_equal']=episode['branches']['median3']['first_trigger_s']==episode['branches']['delay1']['first_trigger_s']
                    rows.append(episode)
                cases.append({'model':model,'seed':seed,'scenario':scenario,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'metadata':meta})
    assert len(rows)==192 and len({(r['model'],r['seed'],r['scenario'],r['env']) for r in rows})==192
    summary=[]
    for scenario in ('Nominal','Stress'):
        selected=[r for r in rows if r['scenario']==scenario]
        summary.append({'scenario':scenario,'episodes':len(selected),
            'native_fell_over':sum(r['termination'].get('fell_over',False) for r in selected),
            'native_time_out':sum(r['termination'].get('time_out',False) for r in selected),
            'native_nan':sum(r['termination'].get('nan_state',False) for r in selected),
            'native_out':sum(r['termination'].get('out_of_terrain_bounds',False) for r in selected),
            'cross_60deg':sum(r['cross_60deg_s'] is not None for r in selected),
            'max_tilt_deg':max(r['max_tilt_deg'] for r in selected),
            'median_delay_first_agreements':sum(r['median_vs_delay_first_equal'] for r in selected),
            'median_delay_all_event_agreements':sum(r['median_vs_delay_all_events_equal'] for r in selected),
            'episodes_with_any_no_foot_contact':sum(r['no_foot_contact_frames']>0 for r in selected),
            'branches':{branch:{'triggered_episodes':sum(bool(r['branches'][branch]['trigger_times_s']) for r in selected),
                'native_falls_without_prior_trigger':sum(r['termination'].get('fell_over',False) and
                    (r['branches'][branch]['first_trigger_s'] is None or r['branches'][branch]['first_trigger_s']>=r['duration_s']) for r in selected)} for branch in branches}})
    cfg=load_env_cfg('Mjlab-Velocity-Flat-MicroDuck',play=True)
    native_fall=cfg.terminations['fell_over']
    result={'complete':True,'cases':cases,'episodes':rows,'summary':summary,
            'native_fall_definition':{'function':native_fall.func.__module__+'.'+native_fall.func.__name__,
                                      'limit_angle_rad':native_fall.params['limit_angle']},
            'provenance':{'commit':subprocess.check_output(['git','-C','/home/deuler/microduck_rl','rev-parse','HEAD'],text=True).strip(),
                'versions':{p:importlib.metadata.version(p) for p in ('torch','mjlab','rsl-rl-lib','mujoco','warp-lang')},
                'files_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('collect_sim_fall_signals.py','analyze_sim_fall_signals.py','SIM_FALL_FILTER_PROTOCOL.md','probe_fall_filter.py')}},
            'scope':'Paired offline predictor replay on official physics, not closed-loop safety intervention',
            'limitations':['Python predictor port, no original Rust execution or IMU packing/fusion.',
               'Pre-reset derived state may lag one physics substep; not hardware synchronization verification.',
               'Foot contacts and native termination are distinct from torso impact; no torso contact sensor.',
               'Runtime startup readiness and recovery controller are not integrated.',
               'Only 10s/16 episodes per model-seed-scenario: pilot, not confirmatory statistics.']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(8,4))
    groups=[[r['max_tilt_deg'] for r in rows if r['model']==m and r['scenario']==s] for m in (42,123,2026) for s in ('Nominal','Stress')]
    ax.boxplot(groups,tick_labels=[f'{m}\n{s}' for m in (42,123,2026) for s in ('Nominal','Stress')])
    ax.axhline(np.rad2deg(np.arccos(.9)),color='orange',linestyle='--',label='Predictor tilt gate (~25.8 deg)')
    ax.axhline(60,color='red',linestyle='--',label='Geometric proxy (not impact)')
    ax.set_ylabel('First-episode max tilt (deg)');ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(OUT/'max_tilt.png',dpi=150);plt.close(fig)
    for row in (r for r in rows if r['termination'].get('fell_over',False)):
        name=f"m{row['model']}_s{row['seed']}_{row['scenario']}"
        data=torch.load(OUT/(name+'.pt'),map_location='cpu',weights_only=True)
        n=row['frames'];env=row['env'];t=(np.arange(n)+1)*.02
        g=data['gravity'][:n,env].numpy();w=data['gyro'][:n,env].numpy()
        gm=median(g,[0,0,-1]);wm=median(w,[0,0,0])
        fig,axes=plt.subplots(3,1,figsize=(9,7),sharex=True)
        axes[0].plot(t,np.rad2deg(np.arccos(np.clip(-g[:,2],-1,1))),label='Raw body tilt')
        axes[0].axhline(60,color='orange',linestyle='--');axes[0].axhline(70,color='red',linestyle='--')
        for branch,bg,bw in (('raw',g,w),('delay1',delay(g,[0,0,-1]),delay(w,[0,0,0])),('median3',gm,wm)):
            _,pred,_=predictor(bg,bw);axes[1].plot(t,pred,label=branch)
            event=row['branches'][branch]['first_trigger_s']
            if event is not None:axes[1].axvline(event,linestyle=':',alpha=.6)
        axes[1].axhline(-.5,color='black',linestyle='--')
        contact=data['contact_found'][:n,env].numpy().reshape(n,-1).astype(bool).sum(axis=1)
        axes[2].step(t,contact,where='post');axes[2].set_ylabel('Foot contact slots')
        axes[0].set_ylabel('Tilt (deg)');axes[1].set_ylabel('Predicted gravity z');axes[1].legend()
        axes[2].set_xlabel('First-episode time (s)');axes[2].set_xlim(max(0,row['duration_s']-.8),row['duration_s'])
        fig.suptitle(f'Official physics trace: {name}, env {env}; offline warnings only')
        fig.tight_layout();fig.savefig(OUT/(name+f'_env{env}_fall.png'),dpi=150);plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
