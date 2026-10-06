"""
Thread stress: keeps starting busy-looping threads until stopped. In standard
CPython the GIL lets only one of them run Python code at a time, so this mostly
raises thread count rather than multi-core CPU load.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import threading

def worker():
    while True:
        pass

while True:
    threading.Thread(target=worker).start()