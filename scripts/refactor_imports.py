import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace unicon.core -> unicon.core
    content = re.sub(r'\bbackend\.core\b', 'unicon.core', content)
    # Replace unicon.instruments -> unicon.instruments
    content = re.sub(r'\bbackend\.drivers\b', 'unicon.instruments', content)
    # Replace unicon.test_wrappers -> unicon.test_wrappers
    content = re.sub(r'\bbackend\.scenarios\b', 'unicon.test_wrappers', content)
    # Replace unicon.dut -> unicon.dut
    content = re.sub(r'\bbackend\.dut\b', 'unicon.dut', content)
    # Replace any leftover unicon. -> unicon.
    content = re.sub(r'\bbackend\.', 'unicon.', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    root_dir = '/Users/swang430/.openclaw/workspace/wideband_performance'
    for subdir, _, files in os.walk(root_dir):
        if '.git' in subdir or 'frontend' in subdir or 'node_modules' in subdir:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                process_file(filepath)
    print("Refactor complete.")
