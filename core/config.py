"""
Central configuration for CrashGuard AI.

Every module imports paths, database settings, the ML feature list and the
alert thresholds from here, so changing a value in this file changes it
everywhere. Database settings can be overridden with environment variables
(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD), which is how Docker
Compose points the app at the `db` container.
"""

import os

# Base paths (resolved from this file, so they work from any working directory)
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CORE_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RUNTIME_DATA_DIR = os.path.join(DATA_DIR, "runtime")
os.makedirs(RUNTIME_DATA_DIR, exist_ok=True)

MODEL_DIRECTORY = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODEL_DIRECTORY, exist_ok=True)

DATASET_PATH = os.path.join(DATA_DIR, "dataset.csv")

# ==========================================================
# Database Configuration
# ==========================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "system_monitoring"),
    "user": os.getenv("DB_USER", "siddhijain"),
    "password": os.getenv("DB_PASSWORD", "Siddhi12")
}

# ==========================================================
# General Configuration
# ==========================================================

COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "5"))

# Legacy model path (kept for compatibility)
MODEL_PATH = os.path.join(MODEL_DIRECTORY, "isolation_forest.pkl")

# ==========================================================
# Database Tables
# ==========================================================

MODEL_FEATURE_TABLE = "model_training_features"
WINDOW_TABLE = "system_feature_windows"
EVENT_TABLE = "system_events"
ANOMALY_TABLE = "anomaly_history"

# ==========================================================
# Machine Learning Configuration
# ==========================================================

# The 29 window features the models are trained on. The ORDER matters: the
# scaler and both models expect columns in exactly this order, and every
# feature builder (web/app.py, scripts/collect_live_physical_data.py,
# pipeline/window_builder.py) produces values under these names.
FEATURE_COLUMNS = [
    "cpu_avg",
    "cpu_max",
    "cpu_min",
    "cpu_std",
    "cpu_trend",
    "cpu_range",
    "cpu_variance",

    "memory_avg",
    "memory_max",
    "memory_min",
    "memory_std",
    "memory_range",
    "memory_trend",

    "disk_avg",
    "disk_max",
    "disk_min",
    "disk_std",
    "disk_range",
    "disk_trend",

    "network_in_avg",
    "network_out_avg",
    "network_in_std",
    "network_out_std",

    "process_avg",
    "process_max",
    "process_min",
    "process_std",

    "running_process_avg",
    "thread_avg"
]

TARGET_COLUMN = "crash_label"

# ==========================================================
# Alert Thresholds
# ==========================================================

# Crash-probability cut-offs used by ml/alert_manager.py.
# Note: RiskPredictor.get_risk_level() uses its own buckets (0.4 / 0.7 / 0.9).
WARNING_THRESHOLD = 0.50
CRITICAL_THRESHOLD = 0.80
