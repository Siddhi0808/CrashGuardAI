"""
Standalone anomaly-detection loop.

Every 5 seconds: read the newest window from system_feature_windows, score it
with the Isolation Forest, store the result in anomaly_history, and write
data/runtime/anomaly_results.json. Runs until interrupted.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import json
import time
import pandas as pd

try:
    from core.config import FEATURE_COLUMNS, WINDOW_TABLE, RUNTIME_DATA_DIR
    from core.db import get_connection
    from ml.model_utils import load_isolation_forest, load_scaler
except ImportError:
    from config import FEATURE_COLUMNS, WINDOW_TABLE
    # db imported above
    # model_utils imported above
    RUNTIME_DATA_DIR = "."
# db imported above
# model_utils imported above

# Load trained model and scaler
model = load_isolation_forest()
scaler = load_scaler()

while True:

    conn = get_connection()

    query = f"""
    SELECT
        {",".join(FEATURE_COLUMNS)}
    FROM {WINDOW_TABLE}
    ORDER BY end_time DESC
    LIMIT 1
    """

    df = pd.read_sql(query, conn)

    if len(df) == 0:
        conn.close()
        time.sleep(5)
        continue

    # Single-host setup: all rows are attributed to host 1
    host_id = 1

    # Scale features
    X_scaled = scaler.transform(df)

    # Predict
    prediction = model.predict(X_scaled)[0]
    score = model.decision_function(X_scaled)[0]

    is_anomaly = bool(prediction == -1)

    # Save prediction to PostgreSQL
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO anomaly_history
        (host_id, anomaly, score)
        VALUES (%s, %s, %s)
    """, (
        host_id,
        is_anomaly,
        float(score)
    ))

    conn.commit()
    cur.close()
    conn.close()

    # Save prediction for dashboard
    result = {
        "prediction": "Anomaly" if is_anomaly else "Normal",
        "anomaly_score": float(score),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    output_path = os.path.join(RUNTIME_DATA_DIR, "anomaly_results.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)

    print(result)

    time.sleep(5)