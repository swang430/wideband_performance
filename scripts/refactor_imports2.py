import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace "from drivers" -> "from unicon.instruments"
    content = re.sub(r'^from drivers\b', 'from unicon.instruments', content, flags=re.MULTILINE)
    # Replace "import drivers" -> "import unicon.instruments"
    content = re.sub(r'^import drivers\b', 'import unicon.instruments', content, flags=re.MULTILINE)
    
    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    root_dir = '/Users/swang430/.openclaw/workspace/wideband_performance/unicon'
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                process_file(filepath)
    print("Refactor 2 complete.")
