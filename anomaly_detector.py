import json
import time
import joblib
import pandas as pd

from db import get_connection
# Load trained model and scaler
model = joblib.load("isolation_forest.pkl")
scaler = joblib.load("scaler.pkl")

while True:

    conn = get_connection()

    query = """
    SELECT
        host_id,
        cpu_usage,
        memory_usage,
        disk_usage,
        network_in,
        network_out,
        process_count,
        running_processes,
        thread_count,
        load_1,
        load_5,
        load_15
    FROM model_training_features
    ORDER BY collected_at DESC
    LIMIT 1
    """

    df = pd.read_sql(query, conn)

    if len(df) == 0:
        conn.close()
        time.sleep(5)
        continue

    # Save host_id separately
    host_id = int(df["host_id"].iloc[0])

    # Drop host_id before prediction
    X = df.drop(columns=["host_id"])

    # Scale features
    X_scaled = scaler.transform(X)

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