import os
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)

from xgboost import XGBClassifier

from db import get_connection

from config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    WINDOW_TABLE
)

from model_utils import (
    save_scaler,
    save_isolation_forest,
    save_xgboost
)


# ==========================================================
# Load Dataset
# ==========================================================

print("Loading training dataset...")

df = None
conn = None

try:
    conn = get_connection()

    query = f"""
    SELECT
        {",".join(FEATURE_COLUMNS)},
        {TARGET_COLUMN}
    FROM {WINDOW_TABLE}
    """

    df = pd.read_sql(query, conn)
    print(f"Loaded {len(df)} samples from database ({WINDOW_TABLE}).")

except Exception as e:
    print(f"Database connection unavailable ({e}). Checking local dataset.csv...")

finally:
    if conn:
        conn.close()

if df is None or df.empty:
    csv_path = "dataset.csv"
    if os.path.exists(csv_path):
        print(f"Loading dataset directly from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} samples from {csv_path}.")
    else:
        raise FileNotFoundError(
            f"Neither database table '{WINDOW_TABLE}' nor '{csv_path}' was found."
        )


# ==========================================================
# Data Cleaning
# ==========================================================

df = df.drop_duplicates()
df = df.dropna()

print(f"Samples after cleaning : {len(df)}")

if df.empty:
    raise ValueError("Training dataset is empty.")


# ==========================================================
# Prepare Features
# ==========================================================

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]

print("\nClass Distribution\n")
print(y.value_counts())

if y.nunique() < 2:
    raise ValueError(
        "Dataset contains only one class. "
        "Run label_windows.py after inserting crash events."
    )


# ==========================================================
# Train Test Split (Temporal Chronological Split)
# ==========================================================

print("\nPartitioning dataset (Chronological 80/20 Temporal Split)...")

split_idx = int(len(df) * 0.80)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"Training samples : {len(X_train)} (Past observations)")
print(f"Test samples     : {len(X_test)} (Future unseen observations)")


# ==========================================================
# Standardization (Fit ONLY on Train to Prevent Data Leakage)
# ==========================================================

print("\nTraining StandardScaler on training partition...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

save_scaler(scaler)

print("✓ Scaler trained (leakage-free)")


# ==========================================================
# Isolation Forest (Unsupervised Anomaly Detection)
# ==========================================================

print("\nTraining Isolation Forest...")

iso = IsolationForest(
    n_estimators=200,
    contamination=0.08,
    random_state=42
)

iso.fit(X_train_scaled)

save_isolation_forest(iso)

print("✓ Isolation Forest trained")


# ==========================================================
# Handle Class Imbalance
# ==========================================================

negative = (y_train == 0).sum()
positive = (y_train == 1).sum()

# Calibrated positive weight to balance precision and recall realistically
scale_weight = min(4.0, max(1.5, (negative / max(1, positive)) * 0.45))

print(f"\nCalibrated Scale Positive Weight : {scale_weight:.2f}")


# ==========================================================
# XGBoost
# ==========================================================

print("\nTraining XGBoost...")

xgb = XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    n_estimators=150,
    learning_rate=0.06,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    scale_pos_weight=scale_weight
)

xgb.fit(
    X_train_scaled,
    y_train
)

save_xgboost(xgb)

print("✓ XGBoost trained")


# ==========================================================
# Evaluation
# ==========================================================

print("\nEvaluating on Unseen Temporal Test Split...\n")

predictions = xgb.predict(X_test_scaled)
probabilities = xgb.predict_proba(X_test_scaled)[:, 1]

print(classification_report(
    y_test,
    predictions
))

print("Confusion Matrix\n")

print(
    confusion_matrix(
        y_test,
        predictions
    )
)

auc = roc_auc_score(
    y_test,
    probabilities
)

print(f"\nROC-AUC : {auc:.4f}")


# ==========================================================
# Feature Importance
# ==========================================================

importance = pd.DataFrame({
    "Feature": FEATURE_COLUMNS,
    "Importance": xgb.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print("\nTop 15 Important Features\n")
print(importance.head(15))


# ==========================================================
# Finished
# ==========================================================

print("\n===================================")
print("Training Completed Successfully")
print("===================================")

print("\nSaved Models")
print("✓ scaler.pkl")
print("✓ isolation_forest.pkl")
print("✓ xgboost.pkl")