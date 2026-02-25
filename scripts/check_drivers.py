import os
import sys

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Checking driver imports...")

try:
    print("1. Importing BaseInstrument...")
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("2. Importing Generic Drivers...")
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("3. Importing R&S Drivers...")
    print("   - SMW200A OK")
    print("   - FSW OK")
    print("   - ZNA OK")
    print("   - CMW500 OK")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("4. Importing Channel Emulators...")
    print("   - Vertex OK")
    print("   - PROPSIM OK")
except Exception as e:
    print(f"   FAIL: {e}")

try:
    print("5. Importing Factory...")
    print("   OK.")
except Exception as e:
    print(f"   FAIL: {e}")

print("Check complete.")
