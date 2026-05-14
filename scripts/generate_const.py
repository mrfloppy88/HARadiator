import json
import re
from pathlib import Path

ROWS = json.loads(Path('/mnt/data/osc_rows.json').read_text())

def expand_address(address):
    addresses = [address]
    if '{N}' in address:
        addresses = [address.replace('{N}', str(n)) for n in (1, 2, 3)]
    if '{A}' in address or '{B}' in address:
        combos = []
        for a in (1, 2, 3):
            for b in (1, 2, 3):
                if a == b:
                    continue
                combos.append(address.replace('{A}', str(a)).replace('{B}', str(b)))
        addresses = combos
    return addresses


def nice_name(address):
    if address == '/radiator/master/blackout':
        return 'Blackout'
    parts = address.replace('/radiator/', '').split('/')
    names = []
    for p in parts:
        p = p.replace('lfo1', 'LFO 1').replace('lfo2', 'LFO 2').replace('lfo3', 'LFO 3')
        p = p.replace('shapeA', 'Shape A').replace('shapeB', 'Shape B')
        p = p.replace('geocorr', 'Geometric correction')
        p = p.replace('mod', 'Mod').replace('p1', 'P1').replace('p2', 'P2').replace('p3', 'P3')
        p = p.replace('_', ' ')
        if p not in {'LFO 1','LFO 2','LFO 3','P1','P2','P3'}:
            p = p.title()
        names.append(p)
    return ' '.join(names)


def parse_range(value_range, typ):
    if value_range is None:
        return None, None, None
    s = str(value_range).replace('−', '-').replace('–', '-').replace('—', '-')
    if typ == 'bool':
        return 0, 1, 1
    # find numbers including decimals
    nums = re.findall(r'-?\d+(?:\.\d+)?', s)
    if len(nums) >= 2 and 'N' not in s:
        mn, mx = float(nums[0]), float(nums[1])
        step = 1 if typ == 'int' else 0.01
        return mn, mx, step
    if len(nums) >= 1 and typ == 'int':
        # 0 - N or 1 - N defaults
        mn = float(nums[0])
        return mn, 255, 1
    return None, None, 1 if typ == 'int' else 0.01

safe_addresses = set([
    '/radiator/master/blackout',
    '/radiator/color/hue','/radiator/color/saturate','/radiator/color/value',
    '/radiator/color/mod/on','/radiator/color/spectral',
    '/radiator/shapeA/on','/radiator/shapeA/size','/radiator/shapeA/speed','/radiator/shapeA/warp',
    '/radiator/shapeB/on','/radiator/shapeB/size','/radiator/shapeB/speed','/radiator/shapeB/warp',
])
for n in (1,2,3):
    safe_addresses.update({
        f'/radiator/lfo{n}/speed', f'/radiator/lfo{n}/level', f'/radiator/lfo{n}/on', f'/radiator/lfo{n}/warp',
    })

number_defs = []
switch_defs = []
sensor_defs = []
all_rx_tx = []
current_section = None

for row in ROWS[1:]:
    addr, direction, typ, rng, notes = (row + [None]*5)[:5]
    if addr and not str(addr).startswith('/'):
        current_section = str(addr)
        continue
    if not addr or not direction or not typ:
        continue
    for expanded in expand_address(addr):
        item = {
            'key': expanded.strip('/').replace('/', '_'),
            'name': nice_name(expanded),
            'address': expanded,
            'value_type': typ,
            'direction': direction,
            'range': rng,
            'notes': notes,
            'section': current_section,
            'enabled_default': expanded in safe_addresses,
        }
        all_rx_tx.append(item)
        if direction == 'TX' or '/name' in expanded or expanded.endswith('/swatch') or expanded.endswith('/current'):
            sensor_defs.append(item)
        elif typ == 'bool':
            switch_defs.append(item)
        elif typ in ('float','int') and expanded != '/radiator/preset':
            mn, mx, step = parse_range(rng, typ)
            item['native_min_value'] = mn
            item['native_max_value'] = mx
            item['native_step'] = step
            number_defs.append(item)

# Clean strings for repr
header = '''"""Constants and OSC entity definitions for HARadiator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DOMAIN: Final = "haradiator"

CONF_SEND_PORT: Final = "send_port"
CONF_LISTEN_HOST: Final = "listen_host"
CONF_LISTEN_PORT: Final = "listen_port"
CONF_PRESET_COUNT: Final = "preset_count"
CONF_EXPOSE_ADVANCED: Final = "expose_advanced"

DEFAULT_SEND_PORT: Final = 9000
DEFAULT_LISTEN_HOST: Final = "0.0.0.0"
DEFAULT_LISTEN_PORT: Final = 9000
DEFAULT_PRESET_COUNT: Final = 16
DEFAULT_EXPOSE_ADVANCED: Final = False

PLATFORMS: Final = ["button", "number", "sensor", "switch"]

ATTR_ADDRESS: Final = "address"
ATTR_VALUE: Final = "value"

SERVICE_SEND_MESSAGE: Final = "send_message"


@dataclass(frozen=True, kw_only=True)
class RadiatorOscDescription:
    """Static description for one Radiator OSC endpoint."""

    key: str
    name: str
    address: str
    value_type: str
    direction: str
    section: str | None = None
    notes: str | None = None
    native_min_value: float | None = None
    native_max_value: float | None = None
    native_step: float | None = None
    entity_registry_enabled_default: bool = False

'''

def desc_list(name, items):
    out = [f'{name}: Final[tuple[RadiatorOscDescription, ...]] = (']
    for it in items:
        fields = {
            'key': it['key'], 'name': it['name'], 'address': it['address'],
            'value_type': it['value_type'], 'direction': it['direction'],
            'section': it.get('section'), 'notes': it.get('notes'),
            'native_min_value': it.get('native_min_value'), 'native_max_value': it.get('native_max_value'),
            'native_step': it.get('native_step'),
            'entity_registry_enabled_default': it.get('enabled_default', False),
        }
        args = ', '.join(f'{k}={v!r}' for k,v in fields.items() if v is not None)
        out.append(f'    RadiatorOscDescription({args}),')
    out.append(')\n')
    return '\n'.join(out)

content = header
content += desc_list('NUMBER_DESCRIPTIONS', number_defs)
content += desc_list('SWITCH_DESCRIPTIONS', switch_defs)
content += desc_list('SENSOR_DESCRIPTIONS', sensor_defs)
content += 'ALL_KNOWN_ADDRESSES: Final[set[str]] = {\n'
for it in all_rx_tx:
    content += f'    {it["address"]!r},\n'
content += '}\n'

Path('/mnt/data/HARadiator_OSC/custom_components/haradiator/const.py').write_text(content)
print(f'Wrote const.py: {len(number_defs)} numbers, {len(switch_defs)} switches, {len(sensor_defs)} sensors')
