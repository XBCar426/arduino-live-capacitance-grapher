import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting Arduino Live Grapher...")

subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])