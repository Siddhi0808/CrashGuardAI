"""
Rule-based alerting on top of RiskPredictor.

Converts a prediction into NORMAL / WARNING / CRITICAL with a message and a
recommendation, using WARNING_THRESHOLD and CRITICAL_THRESHOLD from
core/config.py. Run directly to print the alert for the latest database window.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from datetime import datetime
try:
    from core.config import WARNING_THRESHOLD, CRITICAL_THRESHOLD
    from ml.risk_predictor import predictor
except ImportError:
    from config import WARNING_THRESHOLD, CRITICAL_THRESHOLD
    from risk_predictor import predictor


class AlertManager:

    def __init__(self):
        self.warning_threshold = WARNING_THRESHOLD
        self.critical_threshold = CRITICAL_THRESHOLD

    def generate_alert(self, prediction=None, features=None):
        """
        Build an alert dict.

        Uses `prediction` if given; otherwise predicts from `features`, or from
        the latest database window when neither is given. Falls back to an
        INFO alert when no prediction can be made.
        """
        if prediction is None:
            if features is not None:
                try:
                    prediction = predictor.predict_from_features(features)
                except Exception as e:
                    prediction = None
            else:
                try:
                    prediction = predictor.predict()
                except Exception:
                    prediction = None

        if prediction is None:
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "INFO",
                "risk_level": "UNKNOWN",
                "message": "Collecting telemetry metrics / awaiting feature pipeline.",
                "recommendation": "Ensure data collectors are running.",
                "crash_probability": 0.0,
                "confidence": 0.0,
                "anomaly_score": 0.0,
                "anomaly_flag": False
            }

        probability = prediction.get("crash_probability", 0.0)
        anomaly = prediction.get("anomaly_flag", False)
        anomaly_score = prediction.get("anomaly_score", 0.0)
        confidence = prediction.get("confidence", 0.0)
        risk_level = prediction.get("risk_level", "LOW")
        timestamp = prediction.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        level = "NORMAL"
        message = "System operating normally."
        recommendation = "No action required."

        # Probability thresholds take priority; an Isolation Forest anomaly alone raises a WARNING
        if probability >= self.critical_threshold:
            level = "CRITICAL"
            message = "Critical crash risk detected. Immediate action recommended."
            recommendation = "Investigate CPU, memory and disk usage immediately."
        elif probability >= self.warning_threshold:
            level = "WARNING"
            message = "Crash probability is increasing."
            recommendation = "Monitor system resources and running processes."
        elif anomaly:
            level = "WARNING"
            message = "Anomalous system behaviour detected."
            recommendation = "Review recent system activity."

        return {
            "timestamp": timestamp,
            "level": level,
            "risk_level": risk_level,
            "message": message,
            "recommendation": recommendation,
            "crash_probability": probability,
            "confidence": confidence,
            "anomaly_score": anomaly_score,
            "anomaly_flag": anomaly
        }


alert_manager = AlertManager()


if __name__ == "__main__":
    alert = alert_manager.generate_alert()
    print("\n========== AI SYSTEM ALERT ==========\n")
    print(f"Time               : {alert["timestamp"]}")
    print(f"Alert Level        : {alert["level"]}")
    print(f"Risk Level         : {alert["risk_level"]}")
    print(f"Message            : {alert["message"]}")
    print(f"Recommendation     : {alert["recommendation"]}")
    print(f"Crash Probability  : {alert["crash_probability"]:.2%}")
    print(f"Confidence         : {alert["confidence"]:.2%}")
    print(f"Anomaly Score      : {alert["anomaly_score"]:.4f}")
    print(f"Anomaly Flag       : {alert["anomaly_flag"]}")
