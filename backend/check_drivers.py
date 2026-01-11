import sys
import os

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Checking driver imports...")

try:
    print("1. Importing BaseInstrument...")
    from drivers.base_instrument import BaseInstrument
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("2. Importing Generic Drivers...")
    from drivers.common.generic_vsg import GenericVSG
    from drivers.common.generic_sa import GenericSA
    from drivers.common.generic_vna import GenericVNA
    from drivers.common.generic_tester import GenericTester
    from drivers.common.generic_ce import GenericChannelEmulator
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("3. Importing R&S Drivers...")
    from drivers.rohde_schwarz.smw200a import SMW200A_Driver
    print("   - SMW200A OK")
    from drivers.rohde_schwarz.fsw import FSW_Driver
    print("   - FSW OK")
    from drivers.rohde_schwarz.zna import ZNA_Driver
    print("   - ZNA OK")
    from drivers.rohde_schwarz.cmw500 import CMW500_Driver
    print("   - CMW500 OK")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("4. Importing Channel Emulators...")
    from drivers.spirent.vertex import Vertex_Driver
    print("   - Vertex OK")
    from drivers.keysight.propsim import PROPSIM_Driver
    print("   - PROPSIM OK")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("5. Importing Factory...")
    from drivers.factory import DriverFactory
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

print("Check complete.")
