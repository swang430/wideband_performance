import os

docs_dir = 'docs/api'
os.makedirs(docs_dir, exist_ok=True)

modules = {
    'base_instrument': 'unicon.instruments.base_instrument.BaseInstrument',
    'cmw500': 'unicon.instruments.rohde_schwarz.cmw500.CMW500',
    'mt8000a': 'unicon.instruments.anritsu.mt8000a.MT8000A',
    'smw200a': 'unicon.instruments.rohde_schwarz.smw200a.SMW200A',
    'fsw': 'unicon.instruments.rohde_schwarz.fsw.FSW',
    'mxg': 'unicon.instruments.keysight.mxg.KeysightMXG',
    'vsa': 'unicon.instruments.keysight.vsa.KeysightVSA',
    'ena': 'unicon.instruments.keysight.ena.ENA',
    'pna': 'unicon.instruments.keysight.pna.PNA',
    'zna': 'unicon.instruments.rohde_schwarz.zna.ZNA',
    'vertex': 'unicon.instruments.spirent.vertex.Vertex',
    'propsim': 'unicon.instruments.keysight.propsim.Propsim',
}

for name, path in modules.items():
    with open(f'{docs_dir}/{name}.md', 'w') as f:
        f.write(f'# {name}\n\n::: {path}\n')

with open('docs/index.md', 'w') as f:
    f.write('# Welcome to UniCon\n\nUniversal Control (UniCon) is a pure, high-performance Hardware Abstraction Layer (HAL) for RF T&M instruments.\n\n## Features\n\n- Evidence-based driver development (SCPI references included)\n- Robust PyVISA connections with exponential backoff\n- Native Simulation Mode\n- Asynchronous/Concurrent API support\n')

print("Docs generated.")
