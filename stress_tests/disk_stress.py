"""
Disk stress: writes 1 MB blocks to ./large.bin in the current directory with
no size limit. Stop it with Ctrl+C and delete large.bin afterwards.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

with open("large.bin","wb") as f:
    while True:
        f.write(b"x"*1024*1024)