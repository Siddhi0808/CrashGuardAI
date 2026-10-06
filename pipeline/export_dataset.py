"""
Export labelled windows from system_feature_windows to CSV for offline training.

Note: writes OUTPUT_FILE relative to the current working directory, not to
data/dataset.csv, so it never overwrites the curated training dataset.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd

try:
    from core.config import FEATURE_COLUMNS, TARGET_COLUMN, DATASET_PATH
except ImportError:
    from config import FEATURE_COLUMNS, TARGET_COLUMN
    DATASET_PATH = "data/dataset.csv"
try:
    from core.db import get_connection
except ImportError:
    from db import get_connection


OUTPUT_FILE = "dataset.csv"


def export_dataset():

    conn = None

    try:

        conn = get_connection()

        columns = FEATURE_COLUMNS + [TARGET_COLUMN]

        query = f"""
        SELECT
            {",".join(columns)}
        FROM system_feature_windows
        WHERE {TARGET_COLUMN} IS NOT NULL
        ORDER BY end_time
        """

        df = pd.read_sql(query, conn)

        if df.empty:

            print("No training data found.")
            return

        df = df.dropna()

        df.to_csv(OUTPUT_FILE, index=False)

        positives = int(df[TARGET_COLUMN].sum())
        negatives = len(df) - positives

        print("===================================")
        print("Dataset Export Complete")
        print("===================================")
        print(f"File      : {OUTPUT_FILE}")
        print(f"Rows      : {len(df)}")
        print(f"Features  : {len(FEATURE_COLUMNS)}")
        print(f"Positive  : {positives}")
        print(f"Negative  : {negatives}")

    except Exception as e:

        print("Dataset Export Error:", e)

    finally:

        if conn:
            conn.close()


if __name__ == "__main__":

    export_dataset()