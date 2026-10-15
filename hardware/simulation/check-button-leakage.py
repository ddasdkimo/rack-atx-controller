#!/usr/bin/env python3
"""Bounded DC button-input leakage study; not a motherboard or ESD qualification."""
import hashlib
import itertools
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
circuit = json.loads((ROOT / 'hardware/circuit.json').read_text())
channels = []
for h, button in itertools.product(range(1, 11), ('PWR', 'RST')):
    prefix = f'H{h:02}_{button}'
    tvs = [c for c in circuit['components'] if c['key'] == 'esd' and c['nets']['1'] == prefix + '_A']
    relay = [c for c in circuit['components'] if c['key'] == 'ssr' and set(c['nets'][p] for p in ('4','6')) == {prefix + '_A', prefix + '_B'}]
    assert len(tvs) == len(relay) == 1
    assert tvs[0]['nets'] == {'1': prefix + '_A', '2': prefix + '_B', '3': f'H{h:02}_GND'}
    channels.append({'host': h, 'button': button, 'tvs': tvs[0]['ref'], 'relay': relay[0]['ref']})

rows = []
with tempfile.TemporaryDirectory() as td:
    for supply, pullup, tvs_ua, closed in itertools.product((3.0, 3.3, 5.0), (1000, 10000, 26000, 47000, 100000), (1, 10), (False, True)):
        # One TVS branch per asserted-high signal. The other protected line is
        # host ground in this accepted interface. Relay leakage is independent.
        # An additional 1uA is an explicit allowance for the host input/board.
        total_ua = tvs_ua + (0 if closed else 1) + 1
        ron = 'Rclosed sense 0 2.25' if closed else ''
        deck = f'''Button leakage DC envelope
Vhost supply 0 {supply}
Rpull supply sense {pullup}
Ileak sense 0 {total_ua}u
{ron}
.control
op
print v(sense)
.endc
.end
'''
        path = Path(td) / 'button.cir'; path.write_text(deck)
        result = subprocess.run(['ngspice', '-b', str(path)], capture_output=True, text=True, check=True)
        voltage = float(re.search(r'v\(sense\)\s*=\s*([-+0-9.eE]+)', result.stdout).group(1))
        expected = (supply / pullup - total_ua * 1e-6) / (1 / pullup + (1 / 2.25 if closed else 0))
        assert abs(voltage - expected) < 1e-5
        threshold = supply * (0.3 if closed else 0.7)
        margin = threshold - voltage if closed else voltage - threshold
        accepted = pullup <= 47000
        assert not accepted or margin > 0, (supply, pullup, tvs_ua, closed, voltage)
        rows.append(dict(supply_V=supply, pullup_ohm=pullup, tvs_leakage_uA=tvs_ua,
                         total_leakage_uA=total_ua, closed=closed, voltage_V=voltage,
                         threshold_V=threshold, margin_V=round(margin,6),
                         in_accepted_envelope=accepted, pass_logic=margin > 0))

report = {
    'date': '2026-10-15', 'candidate': 'HXY PESD5V0S2BT / C5451656',
    'decision': 'Accepted for prototype within stated button-interface envelope; not universal motherboard qualification',
    'pass': True, 'method': 'ngspice DC constant-current leakage worst-direction envelope, cross-checked with Ohm law; not vendor SPICE model',
    'circuit_sha256': hashlib.sha256((ROOT/'hardware/circuit.json').read_bytes()).hexdigest(),
    'channels_checked': channels, 'dc_cases': len(rows),
    'accepted_interface': {'button_voltage_V': [3.0, 5.0], 'max_pullup_ohm': 47000,
        'topology': 'Active-low input; one button terminal and HOST_REF verified as the same host ground; A/B may be exchanged',
        'assumed_VIH_fraction': 0.7, 'assumed_VIL_fraction': 0.3,
        'host_input_leakage_allowance_uA': 1, 'closed_path_assumption_ohm': 2.25},
    'datasheet_budget': {'HXY_TVS_max_uA_at_VRWM_5V': 1, 'TLP3122A_max_off_uA_at_60V_Ta25C': 1,
        'combined_added_leakage_uA': 2, 'drop_at_26k_V': 0.052,
        'drop_at_47k_including_1uA_host_allowance_V': 0.141},
    'stress_assumption': {'HXY_leakage_uA': 10, 'interpretation': '10x sensitivity study only; not a measured or guaranteed hot-temperature leakage bound',
        'min_open_margin_in_envelope_V': min(r['margin_V'] for r in rows if r['in_accepted_envelope'] and not r['closed'])},
    'limitations': ['No actual motherboard model supplied; measure idle voltage and pull-up/logic margin before deployment.',
        'HXY document does not give a guaranteed hot-temperature leakage curve; temperature tests remain required.',
        '100k pull-up is exploratory, outside accepted envelope; the 10uA stress fails some cases and is intentionally reported.',
        'Pin3 must remain connected to this host reference. Floating, different-reference, above5V, or unusual bidirectional button circuits are not qualified.',
        'This verifies DC false-press/release margin only; no ESD surge, EMC, thermal or real hardware certification.'],
    'sources': ['https://jlcpcb.com/partdetail/HXYMOSFET-PESD5V0S2BT/C5451656',
        'https://toshiba.semicon-storage.com/info/TLP3122A_datasheet_en_20230525.pdf?did=60353&prodName=TLP3122A',
        'https://edc.intel.com/content/www/us/en/design/platforms/core-processor-series-3-datasheet-volume-1-of-2/001/integrated-pull-ups-and-pull-downs/'],
    'rows': rows,
}
out = ROOT/'hardware/validation/hxy-button-leakage.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(f'PASS: {len(channels)} channel topologies; {len(rows)} DC cases; accepted envelope passes including10xTVS stress. Minimum open margin {report["stress_assumption"]["min_open_margin_in_envelope_V"]:.3f}V.')
print('100k stress failures are outside the accepted envelope; no blanket host/temperature guarantee.')
