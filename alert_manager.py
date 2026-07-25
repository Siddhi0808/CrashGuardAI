from config import (
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD
)

from risk_predictor import predictor


class AlertManager:

    def __init__(self):

        self.warning_threshold = WARNING_THRESHOLD
        self.critical_threshold = CRITICAL_THRESHOLD

    # ==========================================================
    # Generate Alert
    # ==========================================================

    def generate_alert(self):

        prediction = predictor.predict()

        probability = prediction["crash_probability"]
        anomaly = prediction["anomaly_flag"]
        anomaly_score = prediction["anomaly_score"]
        confidence = prediction["confidence"]
        risk_level = prediction["risk_level"]
        timestamp = prediction["timestamp"]

        level = "NORMAL"
        message = "System operating normally."
        recommendation = "No action required."

        if probability >= self.critical_threshold:

            level = "CRITICAL"

            message = (
                "Critical crash risk detected. Immediate action recommended."
            )

            recommendation = (
                "Investigate CPU, memory and disk usage immediately."
            )

        elif probability >= self.warning_threshold:

            level = "WARNING"

            message = (
                "Crash probability is increasing."
            )

            recommendation = (
                "Monitor system resources and running processes."
            )

        elif anomaly:

            level = "WARNING"

            message = (
                "Anomalous system behaviour detected."
            )

            recommendation = (
                "Review recent system activity."
            )

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


# ==========================================================
# Global Alert Manager
# ==========================================================

alert_manager = AlertManager()


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    alert = alert_manager.generate_alert()

    print("\n========== AI SYSTEM ALERT ==========\n")

    print(f"Time               : {alert['timestamp']}")
    print(f"Alert Level        : {alert['level']}")
    print(f"Risk Level         : {alert['risk_level']}")
    print(f"Message            : {alert['message']}")
    print(f"Recommendation     : {alert['recommendation']}")
    print(f"Crash Probability  : {alert['crash_probability']:.2%}")
    print(f"Confidence         : {alert['confidence']:.2%}")
    print(f"Anomaly Score      : {alert['anomaly_score']:.4f}")
    print(f"Anomaly Flag       : {alert['anomaly_flag']}")