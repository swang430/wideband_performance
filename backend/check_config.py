import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config_loader import ConfigLoader

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
print(f"Loading config from: {config_path}")

loader = ConfigLoader(config_path)
config = loader.load()

insts = config.get('instruments', {})
print(f"Loaded {len(insts)} instruments:")
for key in insts:
    print(f" - {key}: {insts[key].get('address')}")
