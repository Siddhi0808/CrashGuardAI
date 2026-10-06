"""
Crash-risk inference.

RiskPredictor loads the three trained artifacts (scaler, Isolation Forest,
XGBoost) and turns one 29-feature window into a crash probability, a risk
level, a margin score and an anomaly flag. A module-level singleton
(`predictor`) is shared by the web app and the alert manager.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import os
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from core.db import get_connection
    from core.config import FEATURE_COLUMNS, WINDOW_TABLE
    from ml.model_utils import (
        load_scaler,
        load_isolation_forest,
        load_xgboost,
        models_exist
    )
except ImportError:
    from db import get_connection
    from config import FEATURE_COLUMNS, WINDOW_TABLE
    from model_utils import (
        load_scaler,
        load_isolation_forest,
        load_xgboost,
        models_exist
    )


class RiskPredictor:
    """Wraps the scaler + Isolation Forest + XGBoost pipeline for live scoring."""

    def __init__(self, eager_load=True):
        # eager_load=False defers disk access until the first prediction
        self.scaler = None
        self.isolation_forest = None
        self.xgboost = None
        if eager_load:
            self.load_models()

    def load_models(self):
        """
        Loads trained models from disk if present.
        """
        try:
            if models_exist():
                self.scaler = load_scaler()
                self.isolation_forest = load_isolation_forest()
                self.xgboost = load_xgboost()
                return True
        except Exception as e:
            print(f"Warning: Could not load ML models ({e}).")
        return False

    @property
    def is_ready(self):
        """True when all three models are loaded; tries to load them lazily if not."""
        if self.scaler is None or self.isolation_forest is None or self.xgboost is None:
            return self.load_models()
        return True

    def get_latest_window(self):
        """
        Fetch latest statistical window from PostgreSQL.
        """
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
        except Exception as e:
            print(f"Could not fetch feature window from database: {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_risk_level(self, probability):
        """Map a crash probability (0-1) to LOW / MEDIUM / HIGH / CRITICAL."""
        if probability >= 0.90:
            return "CRITICAL"
        elif probability >= 0.70:
            return "HIGH"
        elif probability >= 0.40:
            return "MEDIUM"
        return "LOW"

    def get_confidence(self, probability):
        """
        Distance from the 0.5 decision boundary, scaled to 0-1.

        This is a margin score, not a calibrated confidence: p=0.5 -> 0.0,
        p=0.0 or p=1.0 -> 1.0.
        """
        confidence = abs(probability - 0.5) * 2
        return round(float(confidence), 3)

    def predict_from_features(self, features):
        """
        Predict crash risk and anomaly score from a feature DataFrame or dict.
        """
        if not self.is_ready:
            raise RuntimeError("ML models are not trained or loaded yet.")

        if isinstance(features, dict):
            # Ensure all required columns are present, fill missing with 0.0
            row = {col: features.get(col, 0.0) for col in FEATURE_COLUMNS}
            df = pd.DataFrame([row])
        elif isinstance(features, pd.DataFrame):
            df = features[FEATURE_COLUMNS]
        else:
            raise TypeError("Features must be a dictionary or pandas DataFrame.")

        # Apply the same scaling that was fit on the training data
        X = self.scaler.transform(df)

        # Isolation Forest: predict() gives -1 for anomaly / 1 for normal;
        # decision_function() is negative for anomalies (lower = more unusual)
        anomaly_prediction = int(self.isolation_forest.predict(X)[0])
        anomaly_score = float(self.isolation_forest.decision_function(X)[0])
        # XGBoost: probability of class 1 (stress/crash precursor) for the first row
        crash_probability = float(self.xgboost.predict_proba(X)[0][1])

        risk_level = self.get_risk_level(crash_probability)
        confidence = self.get_confidence(crash_probability)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "crash_probability": round(crash_probability, 4),
            "risk_level": risk_level,
            "confidence": confidence,
            "anomaly_score": round(anomaly_score, 4),
            "anomaly_flag": bool(anomaly_prediction == -1)
        }

    def predict(self):
        """
        Default predict: pulls latest window from database.
        """
        df = self.get_latest_window()
        if df is None or df.empty:
            raise ValueError("No feature windows found in database.")
        return self.predict_from_features(df)


# Global Predictor singleton
predictor = RiskPredictor(eager_load=False)


if __name__ == "__main__":
    try:
        predictor.load_models()
        if predictor.is_ready:
            print("✓ ML models ready.")
            try:
                result = predictor.predict()
                print("\\n========== AI Prediction ==========\\n")
                print(f"Time               : {result["timestamp"]}")
                print(f"Crash Probability  : {result["crash_probability"]:.2%}")
                print(f"Risk Level         : {result["risk_level"]}")
                print(f"Confidence         : {result["confidence"]:.2%}")
                print(f"Anomaly Score      : {result["anomaly_score"]}")
                print(f"Anomaly Detected   : {result["anomaly_flag"]}")
            except Exception as e:
                print(f"DB Predict Notice: {e}")
                print("Testing in-memory feature prediction...")
                dummy_features = {col: 0.0 for col in FEATURE_COLUMNS}
                result = predictor.predict_from_features(dummy_features)
                print("In-memory test prediction:", result)
        else:
            print("ML models not found in models/ directory. Run ml/train_model.py first.")
    except Exception as e:
        print(f"Prediction Error: {e}")
