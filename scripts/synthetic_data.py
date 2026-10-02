import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
import pandas as pd

df = pd.read_csv("dataset.csv")

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(df)

model = CTGANSynthesizer(metadata)
model.fit(df)

synthetic = model.sample(30000)

# Make labels mostly positive
positive_ratio = 0.8
n_pos = int(30000 * positive_ratio)
synthetic["crash_label"] = [1] * n_pos + [0] * (30000 - n_pos)
synthetic = synthetic.sample(frac=1, random_state=42)

synthetic.to_csv("synthetic_30000.csv", index=False)