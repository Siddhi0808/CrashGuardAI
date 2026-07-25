import pandas as pd
from datetime import datetime

from db import get_connection

from config import (
    FEATURE_COLUMNS,
    WINDOW_TABLE
)

from model_utils import (
    load_scaler,
    load_isolation_forest,
    load_xgboost
)


class RiskPredictor:

    def __init__(self):

        print("Loading AI models...")

        self.scaler = load_scaler()
        self.isolation_forest = load_isolation_forest()
        self.xgboost = load_xgboost()

        print("✓ AI models loaded.\n")

    # ==========================================================
    # Fetch Latest Window
    # ==========================================================

    def get_latest_window(self):

        conn = None

        try:

            conn = get_connection()

            query = f"""
            SELECT
                {",".join(FEATURE_COLUMNS)}
            FROM {WINDOW_TABLE}
            ORDER BY end_time DESC
            LIMIT 1
            """

            df = pd.read_sql(query, conn)

            return df

        finally:

            if conn:
                conn.close()

    # ==========================================================
    # Convert Probability -> Risk Level
    # ==========================================================

    def get_risk_level(self, probability):

        if probability >= 0.90:
            return "CRITICAL"

        elif probability >= 0.70:
            return "HIGH"

        elif probability >= 0.40:
            return "MEDIUM"

        return "LOW"

    # ==========================================================
    # Prediction Confidence
    # ==========================================================

    def get_confidence(self, probability):

        confidence = abs(probability - 0.5) * 2

        return round(confidence, 3)

    # ==========================================================
    # Predict
    # ==========================================================

    def predict(self):

        df = self.get_latest_window()

        if df is None or df.empty:
            raise Exception("No feature windows found.")

        X = self.scaler.transform(df)

        anomaly_prediction = self.isolation_forest.predict(X)[0]

        anomaly_score = float(
            self.isolation_forest.decision_function(X)[0]
        )

        crash_probability = float(
            self.xgboost.predict_proba(X)[0][1]
        )

        risk_level = self.get_risk_level(
            crash_probability
        )

        confidence = self.get_confidence(
            crash_probability
        )

        return {

            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "crash_probability": round(
                crash_probability,
                4
            ),

            "risk_level": risk_level,

            "confidence": confidence,

            "anomaly_score": round(
                anomaly_score,
                4
            ),

            "anomaly_flag": anomaly_prediction == -1

        }


# ==========================================================
# Global Predictor
# ==========================================================

predictor = RiskPredictor()


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    try:

        result = predictor.predict()

        print("\n========== AI Prediction ==========\n")

        print(f"Time               : {result['timestamp']}")
        print(f"Crash Probability  : {result['crash_probability']:.2%}")
        print(f"Risk Level         : {result['risk_level']}")
        print(f"Confidence         : {result['confidence']:.2%}")
        print(f"Anomaly Score      : {result['anomaly_score']}")
        print(f"Anomaly Detected   : {result['anomaly_flag']}")

    except Exception as e:

        print(f"\nPrediction Error: {e}")