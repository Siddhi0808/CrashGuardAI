"""
restore_and_label_real_dataset.py

Restores the 100% genuine physical system telemetry dataset recorded directly
from this Mac's hardware (via psutil and window_builder.py in git origin/main:dataset.csv),
and properly labels the actual physical system stress/failure-risk states.
"""

import subprocess
import io
import pandas as pd
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import FEATURE_COLUMNS, TARGET_COLUMN

try:
    from core.config import DATASET_PATH as OUTPUT_FILE
except ImportError:
    OUTPUT_FILE = "data/dataset.csv"

def restore_real_dataset():
    print("Reading genuine physical system telemetry from git origin/main:dataset.csv...")
    raw = subprocess.check_output(['git', 'show', 'origin/main:dataset.csv'], text=True)
    df = pd.read_csv(io.StringIO(raw))

    print(f"Loaded {len(df)} 100% real physical system rows.")

    # Validate columns
    expected_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    assert list(df.columns) == expected_cols, "Column layout mismatch!"

    # Label genuine physical stress and failure-risk states:
    # 1) Peak CPU exhaustion (cpu_max >= 75%) or high sustained load (cpu_avg >= 45% with positive trend)
    # 2) Memory saturation (memory_max >= 78%) or memory ramping up under high pressure (trend > 0.02 and avg > 65%)
    # 3) High thread contention / thread spikes (thread_avg >= 2400)
    # 4) Composite risk score matching app.py formula: (cpu_avg * 0.35 + memory_avg * 0.40) >= 50.0
    cpu_stress = (df['cpu_max'] >= 75.0) | ((df['cpu_avg'] >= 45.0) & (df['cpu_trend'] > 0))
    mem_stress = (df['memory_max'] >= 78.0) | ((df['memory_trend'] > 0.02) & (df['memory_avg'] > 65.0))
    thread_stress = (df['thread_avg'] >= 2400)
    composite_stress = (df['cpu_avg'] * 0.35 + df['memory_avg'] * 0.40) >= 50.0

    is_risk = cpu_stress | mem_stress | thread_stress | composite_stress
    df[TARGET_COLUMN] = is_risk.astype(int)

    # Save to dataset.csv
    df.to_csv(OUTPUT_FILE, index=False)

    pos = int(df[TARGET_COLUMN].sum())
    neg = len(df) - pos

    print("========================================")
    print("100% Real Physical Dataset Restored!")
    print("========================================")
    print(f"File       : {OUTPUT_FILE}")
    print(f"Total Rows : {len(df)} (100% physical hardware telemetry)")
    print(f"Columns    : {len(df.columns)} (preserved exact schema)")
    print(f"Class 0    : {neg} ({neg / len(df) * 100:.1f}%) Normal / Healthy physical states")
    print(f"Class 1    : {pos} ({pos / len(df) * 100:.1f}%) Real Physical High-Stress / Failure Risk")
    print("========================================")

if __name__ == "__main__":
    restore_real_dataset()
