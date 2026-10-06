"""
Memory stress: allocates a new ~1 MB string every iteration and keeps it,
so RAM usage grows until the process is killed or the OS runs out of memory.
Stop it with Ctrl+C.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

data = []

while True:
    data.append("A" * 1000000)