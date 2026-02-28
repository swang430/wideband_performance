import sys
import os

if getattr(sys, 'frozen', False):
    print(f"MEIPASS: {sys._MEIPASS}")
    dist_path = os.path.join(sys._MEIPASS, 'frontend', 'dist')
    print(f"Frontend dist path exists: {os.path.exists(dist_path)}")
    if os.path.exists(dist_path):
        print(f"Files in dist: {os.listdir(dist_path)}")
