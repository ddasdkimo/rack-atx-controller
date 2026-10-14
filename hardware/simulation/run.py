#!/usr/bin/env python3
"""Run the B.1 behavioral SPICE study with ngspice and collect results.

Usage: python3 hardware/simulation/run.py [--quick] [--ngspice PATH]

Writes hardware/simulation/results/*.json and updates the "spice_simulation"
section of hardware/validation/checks.json. Behavioral models only; this is
not a vendor-model run and not a substitute for prototype measurements.
"""
import argparse, json, random, re, shutil, subprocess, sys, tempfile, itertools, datetime, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / 'results'
NGSPICE = shutil.which('ngspice') or '/opt/homebrew/bin/ngspice'

MEAS_RE = re.compile(r'^\s*([a-z_0-9]+)\s*=\s*([-+0-9.eE]+|failed)', re.I)
PRINT_RE = re.compile(r'^\s*((?:[iv])\([^)]+\))\s*=\s*([-+0-9.eE]+)', re.I)


def load_deck(name):
    text = (HERE / f'{name}.cir').read_text()
    return text.replace('.include models.lib', f'.include {HERE / "models.lib"}')


def set_params(text, params):
    """Override `.param NAME=value` tokens in the deck header."""
    for key, val in params.items():
        pat = re.compile(r'(\.param\b[^\n]*?\b' + re.escape(key) + r')=([^\s]+)', re.I)
        text, n = pat.subn(lambda m: f'{m.group(1)}={val}', text, count=1)
        if n == 0:
            raise KeyError(f'param {key} not found in deck')
    return text


def run(name, params=None, subs=None, timeout=600):
    text = load_deck(name)
    if params:
        text = set_params(text, params)
    for old, new in (subs or {}).items():
        text = text.replace(old, new)
    with tempfile.TemporaryDirectory() as td:
        deck = Path(td) / f'{name}.cir'
        deck.write_text(text)
        try:
            proc = subprocess.run([NGSPICE, '-b', str(deck)], capture_output=True, text=True,
                                  timeout=timeout, cwd=td)
            out = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            return {'_error': 'timeout'}
    res = {}
    for line in out.splitlines():
        m = PRINT_RE.match(line)
        if m:
            res[m.group(1).lower()] = float(m.group(2))
            continue
        m = MEAS_RE.match(line)
        if m and 'measurement' not in line.lower():
            res[m.group(1).lower()] = None if m.group(2) == 'failed' else float(m.group(2))
    errs = [l for l in out.splitlines() if 'error' in l.lower() and 'measure' not in l.lower()]
    if errs:
        res['_error'] = errs[:3]
    if not res:
        res['_error'] = out[-800:]
    return res


def r3(x, n=4):
    return None if x is None else float(f'{x:.{n}g}')


# --------------------------------------------------------------------------- LED threshold
TH_CORNERS = {
    'KRP': (0.985, 1.015), 'KRG': (0.985, 1.015), 'KRM': (0.985, 1.015), 'KRMG': (0.985, 1.015),
    'KRB': (0.985, 1.015), 'KRF': (0.985, 1.015), 'KRO': (0.985, 1.015),
    'HRAIL': (3.201, 3.399), 'VOS': (-9e-3, 9e-3), 'IB': (0.0, 400e-9), 'IOS': (-150e-9, 150e-9),
    'RON': (100, 175), 'VCM': (0, 5), 'CTR': (1.3, 2.6),
}


def led_threshold(quick):
    out = {'deck': 'led-threshold.cir', 'nominal': {}, 'sensitivity': {}, 'constructed_corners': {}, 'monte_carlo': {}}
    nom = run('led-threshold')
    out['nominal'] = {k: r3(v) for k, v in nom.items()}
    sens = {}
    for key, (lo, hi) in TH_CORNERS.items():
        rl = run('led-threshold', {key: lo})
        rh = run('led-threshold', {key: hi})
        sens[key] = {'low': lo, 'high': hi, 'von_low': r3(rl.get('von')), 'von_high': r3(rh.get('von')),
                     'voff_low': r3(rl.get('voff')), 'voff_high': r3(rh.get('voff'))}
    out['sensitivity'] = sens
    # Build directional worst cases assuming monotonic sensitivity.
    def corner(metric, want_max):
        p = {}
        for key, s in sens.items():
            a, b = s[f'{metric}_low'], s[f'{metric}_high']
            if a is None or b is None:
                continue
            pick_high = (b > a) if want_max else (b < a)
            p[key] = TH_CORNERS[key][1] if pick_high else TH_CORNERS[key][0]
        return p
    for label, metric, want_max in [('von_max', 'von', True), ('von_min', 'von', False),
                                    ('voff_max', 'voff', True), ('voff_min', 'voff', False)]:
        p = corner(metric, want_max)
        r = run('led-threshold', p)
        out['constructed_corners'][label] = {'params': p, 'von': r3(r.get('von')), 'voff': r3(r.get('voff')),
                                             'pledn_low': r3(r.get('pledn_low')), 'pledn_high': r3(r.get('pledn_high')),
                                             'splus_max': r3(r.get('splus_max')), 'sminus_max': r3(r.get('sminus_max'))}
    n = 60 if quick else 300
    rng = random.Random(20261014)
    vons, voffs, hyst = [], [], []
    for _ in range(n):
        p = {k: rng.choice(v) for k, v in TH_CORNERS.items()}
        r = run('led-threshold', p)
        if r.get('von') is not None and r.get('voff') is not None:
            vons.append(r['von']); voffs.append(r['voff']); hyst.append(r['von'] - r['voff'])
    out['monte_carlo'] = {'runs': n, 'valid': len(vons), 'seed': 20261014,
                          'von_min': r3(min(vons)), 'von_max': r3(max(vons)),
                          'voff_min': r3(min(voffs)), 'voff_max': r3(max(voffs)),
                          'hysteresis_min': r3(min(hyst)), 'hysteresis_max': r3(max(hyst))}
    cc = out['constructed_corners']
    out['envelope_V'] = {
        'turn_on': [min(cc['von_min']['von'], out['monte_carlo']['von_min']), max(cc['von_max']['von'], out['monte_carlo']['von_max'])],
        'turn_off': [min(cc['voff_min']['voff'], out['monte_carlo']['voff_min']), max(cc['voff_max']['voff'], out['monte_carlo']['voff_max'])]}
    out['requirement'] = {'off_differential_max_V': 0.2, 'on_differential_min_V': 1.4}
    out['pass'] = out['envelope_V']['turn_on'][1] < 1.4 and out['envelope_V']['turn_off'][0] > 0.2
    return out


# --------------------------------------------------------------------------- LED dynamic
DYN_CASES = {
    'hdd_1ms_green_5V_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m'),
    'hdd_1ms_no_case_led_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', LEDG=0),
    'hdd_1ms_blue_3V3_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', LEDG=0, LEDB=1, VRAIL=3.3),
    'hdd_1ms_green_3V3_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', VRAIL=3.3),
    'hdd_1ms_green_5V_highside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', MODE=1),
    'hdd_1ms_green_5V_2k2_series': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RS='2.2k'),
    'pulse_100us_green_5V': dict(TD='1m', PW='100u', PER='20m', TSTOP='3m'),
    'pulse_30us_green_5V': dict(TD='1m', PW='30u', PER='20m', TSTOP='3m'),
    'pwm_1kHz_20pct_green_5V': dict(TD='1m', PW='200u', PER='1m', TSTOP='21m'),
    'blink_0p5Hz_green_5V': dict(TD='0.5', PW='1', PER='2', TSTOP='3.5'),
    'worst_cmp_ctr_green_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', VOS='9m', IB='400n', RON=175, CTR=1.3, HRAIL=3.201),
    'pushpull_3V3_high_when_off_green_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', MODE=2),
    'whatif_rpu22k_green_5V_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='22k'),
    'whatif_rpu22k_no_case_led_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='22k', LEDG=0),
    'whatif_rpu22k_blue_3V3': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='22k', LEDG=0, LEDB=1, VRAIL=3.3),
    'whatif_rpu22k_highside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='22k', MODE=1),
    'whatif_rpu22k_pushpull': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='22k', MODE=2),
    'whatif_rpu4k7_green_5V_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='4.7k'),
    'whatif_rpu4k7_no_case_led_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='4.7k', LEDG=0),
    'whatif_rpu4k7_green_5V_worst_cmp': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='4.7k', VOS='-9m', IB='400n', HRAIL=3.399),
    'whatif_rpu2k2_green_5V_lowside': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='2.2k'),
    'whatif_rpu2k2_no_case_led_5V': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='2.2k', LEDG=0),
    'whatif_rpu2k2_green_5V_worst_cmp': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='2.2k', VOS='-9m', IB='400n', HRAIL=3.399),
    'whatif_rpu2k2_blue_3V3': dict(TD='1m', PW='1m', PER='20m', TSTOP='5m', RPU='2.2k', LEDG=0, LEDB=1, VRAIL=3.3),
    'whatif_rpu2k2_pwm_1kHz_20pct': dict(TD='1m', PW='200u', PER='1m', TSTOP='21m', RPU='2.2k'),
    'whatif_rpu2k2_pulse_100us': dict(TD='1m', PW='100u', PER='20m', TSTOP='3m', RPU='2.2k'),
}


def _si(v):
    s = str(v).lower()
    mult = {'m': 1e-3, 'u': 1e-6, 'n': 1e-9, 'k': 1e3}
    return float(s[:-1]) * mult[s[-1]] if s[-1] in mult else float(s)


def led_dynamic():
    out = {'deck': 'led-dynamic.cir', 'cases': {}}
    for name, p in DYN_CASES.items():
        r = run('led-dynamic', p)
        c = {'params': p, **{k: r3(v) for k, v in r.items() if not k.startswith('_')}}
        if '_error' in r:
            c['_error'] = r['_error']
        td, pw = _si(p['TD']), _si(p['PW'])
        c['latency_on_s'] = r3(r['t_fall'] - td) if r.get('t_fall') is not None else None
        c['latency_off_s'] = r3(r['t_rise'] - td - pw) if r.get('t_rise') is not None else None
        def state(v):
            return None if v is None else ('on' if v < 0.825 else ('off' if v > 2.475 else 'undefined'))
        c['mcu_reads_while_led_off'] = state(r.get('pledn_off'))
        c['mcu_reads_while_led_on'] = state(r.get('pledn_on'))
        c['detection_correct'] = (c['mcu_reads_while_led_off'] == 'off' and c['mcu_reads_while_led_on'] == 'on')
        out['cases'][name] = c
    out['b1_as_designed_correct'] = [n for n, c in out['cases'].items() if not n.startswith('whatif') and c['detection_correct']]
    out['b1_as_designed_incorrect'] = [n for n, c in out['cases'].items() if not n.startswith('whatif') and not c['detection_correct']]
    return out


# --------------------------------------------------------------------------- LED backfeed
BF_CASES = {
    'host_on_led_on_ctrl_on': dict(VRAIL=5, CTL=1, HRAIL=3.3, C3V3=3.3),
    'host_on_led_off_ctrl_on': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3),
    'host_off_ctrl_on_case_led': dict(VRAIL=0, CTL=0, HRAIL=3.399, C3V3=3.3),
    'host_off_ctrl_on_no_case_led': dict(VRAIL=0, CTL=0, HRAIL=3.399, C3V3=3.3, LEDG=0),
    'host_on_led_on_ctrl_off': dict(VRAIL=5, CTL=1, HRAIL=0, C3V3=0),
    'host_on_led_off_ctrl_off': dict(VRAIL=5, CTL=0, HRAIL=0, C3V3=0),
    'host_on_led_off_ctrl_off_esd_1uA': dict(VRAIL=5, CTL=0, HRAIL=0, C3V3=0, RLEAK_ESD='5meg'),
    'host_on_3V3_led_on_ctrl_off': dict(VRAIL=3.3, CTL=1, HRAIL=0, C3V3=0),
    'host_on_led_off_ctrl_on_highside': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3, MODE=1),
    'host_off_ctrl_on_highside': dict(VRAIL=0, CTL=0, HRAIL=3.399, C3V3=3.3, MODE=1),
    'whatif_rpu22k_host_on_led_off_ctrl_on': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3, RPU='22k'),
    'whatif_rpu22k_host_on_led_on_ctrl_on': dict(VRAIL=5, CTL=1, HRAIL=3.3, C3V3=3.3, RPU='22k'),
    'whatif_rpu22k_host_on_led_on_ctrl_off': dict(VRAIL=5, CTL=1, HRAIL=0, C3V3=0, RPU='22k'),
    'whatif_rpu22k_host_off_ctrl_on': dict(VRAIL=0, CTL=0, HRAIL=3.399, C3V3=3.3, RPU='22k'),
    'whatif_rpu22k_no_case_led_host_on_led_off': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3, RPU='22k', LEDG=0),
    'whatif_rpu2k2_host_on_led_off_ctrl_on': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3, RPU='2.2k'),
    'whatif_rpu2k2_host_on_led_on_ctrl_on': dict(VRAIL=5, CTL=1, HRAIL=3.3, C3V3=3.3, RPU='2.2k'),
    'whatif_rpu2k2_host_on_led_off_ctrl_off': dict(VRAIL=5, CTL=0, HRAIL=0, C3V3=0, RPU='2.2k'),
    'whatif_rpu2k2_host_off_ctrl_on': dict(VRAIL=0, CTL=0, HRAIL=3.399, C3V3=3.3, RPU='2.2k'),
    'whatif_rpu2k2_no_case_led_host_on_led_off': dict(VRAIL=5, CTL=0, HRAIL=3.3, C3V3=3.3, RPU='2.2k', LEDG=0),
}


def led_backfeed():
    out = {'deck': 'led-backfeed.cir', 'cases': {}}
    for name, p in BF_CASES.items():
        q = dict(RLEAK_ESD='50meg'); q.update(p)
        r = run('led-backfeed', q)
        c = {'params': q}
        for k, v in r.items():
            if k.startswith('_'):
                c['_error'] = v
            else:
                c[k] = r3(v)
        if 'i(vip)' in r and 'i(vim)' in r:
            c['into_controller_uA'] = {'led_plus': r3(r['i(vip)'] * 1e6), 'led_minus': r3(r['i(vim)'] * 1e6)}
            c['led_state_seen_by_mcu'] = 'on' if (r.get('v(pledn)', 3.3) < 0.825) else ('off' if r.get('v(pledn)', 0) > 2.475 else 'undefined')
        out['cases'][name] = c
    return out


# --------------------------------------------------------------------------- Photorelay
def photorelay():
    out = {'deck': 'photorelay.cir', 'nominal': {}, 'corners': {}, 'off_states': {}}
    nom = run('photorelay')
    out['nominal'] = {k: r3(v) for k, v in nom.items() if not k.startswith('_')}
    ifs = []
    worst = {}
    for v5, vdrv, k220, k1500, vf, q, nch in itertools.product((4.75, 5.25), (2.9, 3.3), (0.99, 1.01), (0.99, 1.01), (-0.17, 0.13), ('LO', 'HI'), (1, 20)):
        p = dict(V5=v5, VDRV=vdrv, K220=k220, K1500=k1500, VFADJ=vf, NCH=nch)
        r = run('photorelay', p, subs={'MMBT3904_TYP': f'MMBT3904_{q}'})
        i_f = r.get('i(v.xu10.vsens)')
        if i_f is None:
            continue
        closed = r.get('v(h_pwr_a,h_pwr_b)', 9) < 0.1
        ifs.append((i_f, closed, {**p, 'Q': q}))
    ifs.sort(key=lambda t: t[0])
    out['corners'] = {'runs': len(ifs), 'if_min_mA': r3(ifs[0][0] * 1e3), 'if_min_params': ifs[0][2],
                      'if_max_mA': r3(ifs[-1][0] * 1e3), 'if_max_params': ifs[-1][2],
                      'all_closed_with_IFT_3mA': all(c for _, c, _ in ifs),
                      'margin_to_IFT_3mA_min_mA': r3((ifs[0][0] - 3e-3) * 1e3),
                      'margin_to_IF_abs_max_50mA_mA': r3((50e-3 - ifs[-1][0]) * 1e3)}
    for name, p in {'drv_low': dict(LEVEL=0), 'drv_tristate_oe_high': dict(OE=0),
                    'drv_tristate_20ch_rail_loaded': dict(OE=0, NCH=20)}.items():
        r = run('photorelay', p)
        out['off_states'][name] = {k: r3(v) for k, v in r.items() if not k.startswith('_')}
        out['off_states'][name]['relay_open'] = r.get('v(h_pwr_a,h_pwr_b)', 0) > 3.0
    return out


# --------------------------------------------------------------------------- Timer
def timer(quick):
    out = {'deck': 'timer.cir', 'nominal': {}, 'corners': [], 'behaviour': {}}
    nom = run('timer', dict(TSTOP=40))
    out['nominal'] = {k: r3(v) for k, v in nom.items() if not k.startswith('_')}
    # Capacitance assumptions for 3 x CL21A106KAYNNNE (10 uF 25 V X5R 0805): tolerance +/-10 %,
    # DC bias at 5 V assumed -25 % worst, X5R temperature -15 % at the 0..70 C limits.
    ct_min, ct_max = 30e-6 * 0.9 * 0.75 * 0.85, 30e-6 * 1.1
    corners = []
    kth = (2.7 / 3.3333, 3.9 / 3.3333)
    for ct, kr, kt in itertools.product((ct_min, ct_max), (0.99, 1.01), kth):
        r = run('timer', dict(CT=f'{ct:.4e}', KR32=kr, KTH=f'{kt:.4f}', TSTOP=60))
        corners.append({'CT_uF': r3(ct * 1e6), 'KR32': kr, 'VIT_V': r3(kt * 3.3333), 'pulse_s': r3(r.get('pulse_w'))})
    out['corners'] = corners
    widths = [c['pulse_s'] for c in corners if c['pulse_s'] is not None]
    out['pulse_range_s'] = [r3(min(widths)), r3(max(widths))]
    out['capacitance_assumption_uF'] = [r3(ct_min * 1e6), r3(ct_max * 1e6)]
    out['qualification_target_s'] = [8, 25]
    out['pulse_within_target'] = min(widths) >= 8 and max(widths) <= 25
    beh = {}
    r = run('timer', dict(FIRE_PW=100, TSTOP=40))
    beh['fire_held_high_40s'] = {'pulse_s': r3(r.get('pulse_w')), 'on_total_s': r3(r.get('on_total')), 'note': 'edge-coupled trigger: a held FIRE level must not extend the pulse'}
    r = run('timer', dict(FIRE_PW='1m', FIRE_PER=5, TSTOP=60))
    beh['retrigger_every_5s_1ms'] = {'first_pulse_s': r3(r.get('pulse_w')), 'on_total_s': r3(r.get('on_total')), 'last_off_s': r3(r.get('t_last_off')), 'last_on_s': r3(r.get('t_last_on'))}
    r = run('timer', dict(FIRE_PW='1m', FIRE_PER=1, TSTOP=60))
    beh['retrigger_every_1s_1ms'] = {'first_pulse_s': r3(r.get('pulse_w')), 'on_total_s': r3(r.get('on_total')), 'last_off_s': r3(r.get('t_last_off'))}
    r = run('timer', dict(ARM_PW='5.05', TSTOP=20))
    beh['arm_dropped_5s_after_fire'] = {'t_on_s': r3(r.get('t_on')), 't_off_s': r3(r.get('t_off')), 'pulse_s': r3(r.get('pulse_w'))}
    r = run('timer', dict(ARM_T=100, TSTOP=5))
    beh['fire_while_disarmed'] = {'photo_5v_max_V': r3(r.get('photo_5v_max')), 'rail_stays_off': (r.get('photo_5v_max') or 9) < 0.5}
    r = run('timer', dict(RLOAD=29, TSTOP=5))
    beh['rail_20_channels_29ohm'] = {'photo_5v_max_V': r3(r.get('photo_5v_max'))}
    r = run('timer', dict(V5=4.75, KTH=f'{kth[1]:.4f}', TSTOP=5))
    beh['trigger_pulse_4V75_worst'] = {'trig_pw_s': r3(r.get('trig_pw')), 'trig_n_min_V': r3(r.get('trig_n_min')), 'trig_base_min_V': r3(r.get('trig_base_min'))}
    out['behaviour'] = beh
    return out


# --------------------------------------------------------------------------- Power-up
def powerup():
    out = {'deck': 'powerup.cir', 'cases': {}}
    cases = {
        'as_designed_gpio43_44_wpu_45k': dict(),
        'as_designed_vrst_1V8_worst': dict(VRST=1.8),
        'as_designed_firmware_late_1s': dict(TFW=1.0),
        'as_designed_slow_5V_ramp_100ms': dict(TRAMP='100m', TGL='102m'),
        'as_designed_wpu_30k': dict(RWPU='30k'),
        'if_timer_pins_had_no_pullup': dict(RWPU='1e12'),
        'hypothetical_fast_edge_on_fire_at_50ms': dict(TFG='50m'),
        'hypothetical_fast_edge_on_fire_plus_oe_glitch_same_time': dict(TFG='50m', TGL='50.5m'),
        'hypothetical_fast_edge_plus_oe_glitch_ideal_relay_switch': dict(TFG='50m', TGL='50.5m', TON_TAU='1n'),
        'if_timer_pins_had_no_pullup_fast_edge_on_fire': dict(RWPU='1e12', TFG='50m'),
    }
    for name, p in cases.items():
        r = run('powerup', p, timeout=900)
        c = {'params': p, **{k: r3(v) for k, v in r.items() if not k.startswith('_')}}
        if '_error' in r:
            c['_error'] = r['_error']
        c['rail_enabled_during_boot'] = (r.get('rail_on_total') or 0) > 0.01
        c['relay_closed_total_s'] = r3(r.get('closed_total'))
        out['cases'][name] = c
    return out


def update_checks(summary):
    """Write a compact summary into hardware/validation/checks.json (key spice_simulation)."""
    st = summary['studies']
    th, dy, bf, pr, tm, pu = (st.get(k, {}) for k in ('led-threshold', 'led-dynamic', 'led-backfeed', 'photorelay', 'timer', 'powerup'))
    def bfc(name, key):
        return bf.get('cases', {}).get(name, {}).get(key)
    compact = {
        'date': summary['date'], 'simulator': summary['simulator'], 'method': summary['method'],
        'status': 'behavioral models, datasheet-fitted; not vendor models; no hardware correlation; findings are review input, not adopted circuit changes',
        'results_dir': 'hardware/simulation/results/',
        'led_threshold_envelope_V': th.get('envelope_V'),
        'led_threshold_monte_carlo_runs': th.get('monte_carlo', {}).get('runs'),
        'led_threshold_pass_for_ideal_envelope': th.get('pass'),
        'led_detection_correct_cases_b1': dy.get('b1_as_designed_correct'),
        'led_detection_incorrect_cases_b1': dy.get('b1_as_designed_incorrect'),
        'led_off_state_differential_V_lowside_green_5V': dy.get('cases', {}).get('hdd_1ms_green_5V_lowside', {}).get('vdiff_off'),
        'led_off_state_differential_V_no_case_led_5V': dy.get('cases', {}).get('hdd_1ms_no_case_led_5V', {}).get('vdiff_off'),
        'led_latency_on_s_highside_green': dy.get('cases', {}).get('hdd_1ms_green_5V_highside', {}).get('latency_on_s'),
        'led_latency_off_s_highside_green': dy.get('cases', {}).get('hdd_1ms_green_5V_highside', {}).get('latency_off_s'),
        'backfeed_into_unpowered_host_uA': bfc('host_off_ctrl_on_case_led', 'into_controller_uA'),
        'loading_by_unpowered_controller_uA_led_off': bfc('host_on_led_off_ctrl_off', 'into_controller_uA'),
        'case_led_current_uA_when_motherboard_driver_off_lowside': (bfc('host_on_led_off_ctrl_off', 'into_controller_uA') or {}).get('led_minus'),
        'photorelay_if_range_mA': [pr.get('corners', {}).get('if_min_mA'), pr.get('corners', {}).get('if_max_mA')],
        'photorelay_all_corners_close_at_IFT_3mA': pr.get('corners', {}).get('all_closed_with_IFT_3mA'),
        'photorelay_off_states_open': all(v.get('relay_open') for v in pr.get('off_states', {}).values()) if pr.get('off_states') else None,
        'timer_pulse_range_s': tm.get('pulse_range_s'),
        'timer_capacitance_assumption_uF': tm.get('capacitance_assumption_uF'),
        'timer_pulse_within_8_25s_target': tm.get('pulse_within_target'),
        'timer_held_fire_does_not_extend': (tm.get('behaviour', {}).get('fire_held_high_40s', {}).get('on_total_s') is not None and tm.get('behaviour', {}).get('fire_held_high_40s', {}).get('pulse_s') is not None),
        'timer_retrigger_5s_on_total_s': tm.get('behaviour', {}).get('retrigger_every_5s_1ms', {}).get('on_total_s'),
        'powerup_timer_arm_pin_V_during_boot': pu.get('cases', {}).get('as_designed_gpio43_44_wpu_45k', {}).get('arm_max'),
        'powerup_rail_enabled_as_designed': pu.get('cases', {}).get('as_designed_gpio43_44_wpu_45k', {}).get('rail_enabled_during_boot'),
        'powerup_rail_enabled_if_fast_edge_on_fire': pu.get('cases', {}).get('hypothetical_fast_edge_on_fire_at_50ms', {}).get('rail_enabled_during_boot'),
        'powerup_relay_closed_s_fast_edge_plus_oe_glitch': pu.get('cases', {}).get('hypothetical_fast_edge_on_fire_plus_oe_glitch_same_time', {}).get('relay_closed_total_s'),
    }
    path = ROOT / 'hardware/validation/checks.json'
    data = json.loads(path.read_text()) if path.exists() else {}
    data['spice_simulation'] = compact
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return compact


def main():
    global NGSPICE
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--ngspice', default=None)
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    if args.ngspice:
        NGSPICE = args.ngspice
    RESULTS.mkdir(exist_ok=True)
    ver = subprocess.run([NGSPICE, '-v'], capture_output=True, text=True).stdout.splitlines()
    ver = next((l.strip('* ').strip() for l in ver if 'ngspice' in l.lower()), 'ngspice')
    jobs = {'led-threshold': lambda: led_threshold(args.quick), 'led-dynamic': led_dynamic,
            'led-backfeed': led_backfeed, 'photorelay': photorelay, 'timer': lambda: timer(args.quick), 'powerup': powerup}
    summary = {'revision': 'B.1', 'date': datetime.date.today().isoformat(), 'simulator': ver,
               'method': 'ngspice batch runs of behavioral, datasheet-fitted models; no vendor models, no hardware correlation',
               'models_sha256': hashlib.sha256((HERE / 'models.lib').read_bytes()).hexdigest()[:16], 'studies': {}}
    for name, fn in jobs.items():
        if args.only and name not in args.only.split(','):
            prev = RESULTS / f'{name}.json'
            if prev.exists():
                summary['studies'][name] = json.loads(prev.read_text())
            continue
        print('running', name, flush=True)
        res = fn()
        (RESULTS / f'{name}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
        summary['studies'][name] = res
    (RESULTS / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n')
    update_checks(summary)
    print('done')


if __name__ == '__main__':
    main()
