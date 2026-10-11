"""Read-only result/checkpoint validation, plus a new factual validation artifact."""
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'full_width_clean_recovery'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    data=json.loads((OUT/'results.json').read_text())
    summary=json.loads((OUT/'summary.json').read_text())
    assert data['complete'] and summary['complete']
    assert len(data['training'])==len(data['gates'])==10
    expected=20+4*sum(g['nominal_gate_passed'] for g in data['gates'])
    assert len(data['cases'])==data['expected_cases_after_gates']==summary['case_count']==expected==60
    assert len({(r['teacher'],r['branch'],r['eval_seed'],r['pitch_degrees']) for r in data['cases']})==60
    assert all(len(r['rows'])==64 and r['state_unchanged'] for r in data['cases'])
    assert all(math.isfinite(row[k]) for r in data['cases'] for row in r['rows'] for k in ('seconds','return','mean_vx_error','mean_vy_error','mean_yaw_error','mean_action_delta'))
    assert sum(r['survival_count'] for r in data['cases'])==3840
    assert sum(r['nan_count'] for r in data['cases'])==sum(r['out_count'] for r in data['cases'])==0
    assert all(r['immutable_state_unchanged'] for r in data['training'])
    for teacher in (42,2026):
        assert len({r['clean_sample_schedule_sha256'] for r in data['training'] if r['teacher']==teacher})==1
    parents=ROOT/'full_width_order_pilot'
    assert sha(parents/'results.json')==data['source_results_sha256']
    checked=0
    for directory in (parents,OUT):
        inventory=json.loads((directory/'artifact_inventory.json').read_text())
        for row in inventory['files']:
            assert sha(directory/row['file'])==row['sha256'],row['file']
            checked+=1
    runs={42:'2026-09-21_21-57-05_walk_baseline_4096_seed42_4000_v2',2026:'2026-09-29_10-44-28_walk_baseline_4096_seed2026_4000_v1_resume3250_quiet'}
    model_checks={}
    for seed,run in runs.items():
        original=Path('/home/deuler/microduck_rl/logs/rsl_rl/velocity')/run/'model_3999.pt'
        clone=ROOT/'ppo_clone_baseline'/f'seed{seed}_clone_model3999.pt'
        model_checks[str(seed)]=sha(original)
        assert sha(original)==sha(clone)
    audit={'complete':True,'cases':60,'episodes':3840,'survival_count':3840,'nan_count':0,'terrain_exit_count':0,
           'finite_episode_metrics':True,'unique_cases':True,'fixed_normalization_state_verified_by_training_and_eval':True,
           'parent_and_current_inventory_files_checked':checked,'original_checkpoints_unchanged':model_checks,
           'versions':{n:importlib.metadata.version(n) for n in ('torch','mjlab','rsl-rl-lib','mujoco','warp-lang')},
           'scripts_sha256':{n:sha(ROOT/n) for n in ('run_common_clean_recovery.py','analyze_common_clean_recovery.py','verify_clean_recovery_completion.py','COMMON_CLEAN_RECOVERY_PROTOCOL.md','ORDER_PILOT_FINAL_DECISION.md')}}
    (OUT/'completion_validation.json').write_text(json.dumps(audit,indent=2))
    inventory={'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('artifact_inventory.json','run.log','process.json')]}
    (OUT/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2))
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
