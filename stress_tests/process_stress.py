"""
Process stress: spawns `sleep 300` child processes in an endless loop to
exhaust the process table. Use with care; stop with Ctrl+C.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import subprocess

while True:
    subprocess.Popen(["sleep", "300"])