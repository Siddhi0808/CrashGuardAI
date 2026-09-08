import json
import time
import pandas as pd

from config import FEATURE_COLUMNS, WINDOW_TABLE
from db import get_connection
from model_utils import load_isolation_forest, load_scaler

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

    with open("anomaly_results.json", "w") as f:
        json.dump(result, f, indent=4)

    print(result)

    time.sleep(5)