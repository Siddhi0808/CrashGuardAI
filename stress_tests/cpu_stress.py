"""
CPU stress: an infinite busy loop that saturates one CPU core.
Runs until killed (Ctrl+C).
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

while True:
    pass