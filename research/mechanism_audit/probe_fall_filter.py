"""Kinematic diagnostic, not robot dynamics or original Rust execution."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'fall_filter_probe'
DT = .02
T = np.arange(301) * DT


def predictor(g, w):
    rate = -(w[:, 0] * g[:, 1] - w[:, 1] * g[:, 0])
    pred = g[:, 2] + .3 * rate
    cond = (g[:, 2] > -.9) & (rate > 0) & (pred > -.5)
    ticks, fired, events = 0, False, []
    for i, yes in enumerate(cond):
        if not yes:
            ticks, fired = 0, False
        else:
            ticks += 1
            if ticks >= 3 and not fired:
                events.append(i)
                fired = True
    return rate, pred, events


def delay(a, initial):
    return np.vstack([initial, a[:-1]])


def median(a, initial):
    d1 = delay(a, initial)
    return np.median(np.stack([a, d1, delay(d1, initial)]), axis=0)


def unit_checks():
    def constant(angle, speed, count=50):
        return predictor(np.tile([np.sin(angle), 0, -np.cos(angle)], (count, 1)),
                         np.tile([0, speed, 0], (count, 1)))
    assert abs(constant(np.pi/6, 1)[0][0] - .5) < 1e-12
    for a, s in ((.9, -4), (.14, 3), (1.2, 0), (.46, .3)):
        assert not constant(a, s)[2]
    assert constant(.6, 3)[2] == [2]


def main():
    OUT.mkdir(exist_ok=True)
    src = ROOT.parent / 'upstream_audit/microduck_runtime/duck-control/src/fall.rs'
    text = src.read_text()
    for contract in ('tilt_z: -0.90', 'predicted_z: -0.5',
                     'Duration::from_millis(300)', 'Duration::from_millis(60)',
                     '-(imu.gyro[0] * imu.gravity[1] - imu.gyro[1] * imu.gravity[0])'):
        assert contract in text, 'Upstream changed: re-audit required'
    unit_checks()
    trajectories = []
    for peak in (65, 75, 85):
        for duration in (.5, 1., 2.):
            u = np.clip((T-1)/duration, 0, 1)
            theta = np.deg2rad(peak)*(.5-.5*np.cos(np.pi*u))
            speed = np.deg2rad(peak)*.5*np.pi/duration*np.sin(np.pi*u)
            trajectories.append((f'ramp_{peak}_{duration}', theta, speed))
    for amp in (8, 30, 50):
        for frequency in (.5, 1, 2, 3):
            for sign in (-1, 1):
                # C1 envelope after a 1s upright warm-up.
                s = np.maximum(T-1, 0)
                u = np.clip(s, 0, 1)
                e = .5-.5*np.cos(np.pi*u)
                ed = .5*np.pi*np.sin(np.pi*u)
                k = 2*np.pi*frequency
                a = sign*np.deg2rad(amp)
                trajectories.append((f'osc_{amp}_{frequency}_{sign}',
                                     a*e*np.sin(k*s), a*(ed*np.sin(k*s)+e*k*np.cos(k*s))))
    for duration in (.3, .6, 1.2):
        s = T-1
        inside = (s >= 0) & (s <= duration)
        u = np.clip(s/duration, 0, 1)
        a = np.deg2rad(40)
        trajectories.append((f'recover_40_{duration}',
                             a*np.sin(np.pi*u)**2,
                             np.where(inside, a*np.pi/duration*np.sin(2*np.pi*u), 0)))
    for angle in (0, 20, 40, 55):
        trajectories.append((f'static_{angle}', np.full_like(T, np.deg2rad(angle)), np.zeros_like(T)))
    assert len(trajectories) == 40
    records, arrays = [], {}
    for name, theta, speed in trajectories:
        g = np.column_stack([np.sin(theta), np.zeros_like(T), -np.cos(theta)])
        w = np.column_stack([np.zeros_like(T), speed, np.zeros_like(T)])
        gd, wd = delay(g, g[0]), delay(w, w[0])
        gm, wm = median(g, g[0]), median(w, w[0])
        branches = {'raw': (g, w), 'delay1': (gd, wd), 'median3': (gm, wm),
                    'median3_unit': (gm/np.linalg.norm(gm, axis=1)[:, None], wm),
                    'gyro_delay1': (g, wd), 'gravity_delay1': (gd, w)}
        crossed = np.flatnonzero(g[:, 2] > -.5)
        cross = int(crossed[0]) if len(crossed) else None
        truth_rate = speed*np.sin(theta)
        assert np.allclose(-np.cross(w, g)[:, 2], truth_rate)
        for branch, (bg, bw) in branches.items():
            rate, pred, events = predictor(bg, bw)
            first = events[0] if events else None
            reference = truth_rate if branch == 'raw' else np.r_[truth_rate[0], truth_rate[:-1]]
            # For independently delayed pairs this reference is diagnostic, not exact truth.
            rec = {'trajectory': name, 'branch': branch, 'cross_time_s': None if cross is None else cross*DT,
                   'all_trigger_times_s': [i*DT for i in events],
                   'first_trigger_s': None if first is None else first*DT,
                   'lead_s': None if cross is None or first is None else (cross-first)*DT,
                   'trigger_without_crossing': cross is None and first is not None,
                   'no_advance_warning': cross is not None and (first is None or first >= cross),
                   'matched_delay_rate_rmse': float(np.sqrt(np.mean((rate-reference)**2))),
                   'max_abs_pitch_rate_rad_s': float(np.abs(speed).max())}
            records.append(rec)
            arrays[name+'__'+branch] = np.column_stack([T, bg, bw, rate, pred])
    summary = {}
    for branch in branches:
        rows = [r for r in records if r['branch'] == branch]
        lead = [r['lead_s'] for r in rows if r['lead_s'] is not None]
        summary[branch] = {'cases': len(rows),
                           'triggers_without_crossing': sum(r['trigger_without_crossing'] for r in rows),
                           'no_advance_warning': sum(r['no_advance_warning'] for r in rows),
                           'mean_lead_s': float(np.mean(lead)) if lead else None,
                           'mean_matched_delay_rate_rmse': float(np.mean([r['matched_delay_rate_rmse'] for r in rows]))}
    paired = []
    for name, _, _ in trajectories:
        rows = {r['branch']: r for r in records if r['trajectory'] == name}
        a, b = rows['median3']['first_trigger_s'], rows['delay1']['first_trigger_s']
        paired.append({'trajectory': name, 'same_trigger': a == b,
                       'same_all_trigger_times': rows['median3']['all_trigger_times_s'] == rows['delay1']['all_trigger_times_s'],
                       'median_minus_delay_s': None if a is None or b is None else a-b})
    assert len(records) == len({(r['trajectory'], r['branch']) for r in records}) == 240
    assert all(np.isfinite(a).all() for a in arrays.values())
    result = {'complete': True, 'cases': 240, 'summary': summary, 'records': records,
              'paired': paired, 'median_delay_exact_trigger_agreements': sum(p['same_trigger'] for p in paired),
              'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
              'protocol_sha256': hashlib.sha256((ROOT/'FALL_FILTER_PROTOCOL.md').read_bytes()).hexdigest(),
              'implementation': 'Python port, numerical official-test checks; no Rust compiler available',
              'limitations': ['Synthetic single-axis kinematics; no rigid-body/contact dynamics.',
                              '60deg threshold crossing is not ground-truth robot fall.',
                              'No quaternion packing, sensor fusion, noise, or hardware calibration.',
                              'Static cases use settled histories, unlike upright-start moving cases.',
                              'No weights, action policies, closed-loop control, or safety intervention.']}
    np.savez_compressed(OUT/'traces.npz', **arrays)
    (OUT/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for branch in ('raw', 'delay1', 'median3', 'median3_unit'):
        v = arrays['ramp_75_0.5__'+branch]
        axes[0].plot(v[:, 0], v[:, 3], label=branch)
        axes[1].plot(v[:, 0], v[:, -1], label=branch)
    axes[0].axhline(-.5, color='black', linestyle='--')
    axes[1].axhline(-.5, color='black', linestyle='--')
    axes[0].set_ylabel('Gravity z'); axes[1].set_ylabel('Predicted gravity z')
    axes[1].set_xlabel('Time (s)'); axes[0].legend(); axes[1].set_xlim(.9, 1.7)
    fig.suptitle('Kinematic probe only: not a simulated robot fall')
    fig.tight_layout(); fig.savefig(OUT/'prediction_comparison.png', dpi=150); plt.close(fig)
    print(json.dumps({'summary': summary, 'median_delay_exact_trigger_agreements': result['median_delay_exact_trigger_agreements']}, indent=2))


if __name__ == '__main__':
    main()
