import os

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

COLLECTION_INTERVAL = 5

# Legacy model path (kept for compatibility)
MODEL_PATH = "isolation_forest_model.pkl"

# Directory where all ML models are stored
MODEL_DIRECTORY = "models"

# ==========================================================
# Database Tables
# ==========================================================

MODEL_FEATURE_TABLE = "model_training_features"

WINDOW_TABLE = "system_feature_windows"

EVENT_TABLE = "system_events"

# ==========================================================
# Machine Learning Configuration
# ==========================================================

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

WARNING_THRESHOLD = 0.50

CRITICAL_THRESHOLD = 0.80