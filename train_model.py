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

finally:
    if conn:
        conn.close()

print(f"Loaded {len(df)} samples.")


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
# Standardization
# ==========================================================

print("\nTraining StandardScaler...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

save_scaler(scaler)

print("✓ Scaler trained")


# ==========================================================
# Isolation Forest
# ==========================================================

print("\nTraining Isolation Forest...")

iso = IsolationForest(
    n_estimators=300,
    contamination=0.02,
    random_state=42
)

iso.fit(X_scaled)

save_isolation_forest(iso)

print("✓ Isolation Forest trained")


# ==========================================================
# Train Test Split
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.20,
    stratify=y,
    random_state=42
)


# ==========================================================
# Handle Class Imbalance
# ==========================================================

negative = (y_train == 0).sum()
positive = (y_train == 1).sum()

if positive == 0:
    scale_weight = 1.0
else:
    scale_weight = negative / positive

print(f"\nScale Positive Weight : {scale_weight:.2f}")


# ==========================================================
# XGBoost
# ==========================================================

print("\nTraining XGBoost...")

xgb = XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    n_estimators=300,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    scale_pos_weight=scale_weight
)

xgb.fit(
    X_train,
    y_train
)

save_xgboost(xgb)

print("✓ XGBoost trained")


# ==========================================================
# Evaluation
# ==========================================================

print("\nEvaluating...\n")

predictions = xgb.predict(X_test)
probabilities = xgb.predict_proba(X_test)[:, 1]

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