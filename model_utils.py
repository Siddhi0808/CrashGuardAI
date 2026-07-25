import os
import joblib

from config import MODEL_DIRECTORY


# ==========================================================
# Model Cache
# ==========================================================

_model_cache = {}


# ==========================================================
# Directory Helpers
# ==========================================================

def ensure_models_directory():
    """
    Create models directory if it doesn't exist.
    """
    os.makedirs(MODEL_DIRECTORY, exist_ok=True)


def get_model_path(filename):
    """
    Returns the full path of a model file.
    """
    ensure_models_directory()
    return os.path.join(MODEL_DIRECTORY, filename)


# ==========================================================
# Generic Save / Load
# ==========================================================

def save_model(model, filename):
    """
    Save any ML model and refresh cache.
    """

    path = get_model_path(filename)

    joblib.dump(model, path)

    _model_cache[filename] = model

    print(f"✓ Saved: {path}")


def load_model(filename):
    """
    Load model from cache if available,
    otherwise load from disk.
    """

    if filename in _model_cache:
        return _model_cache[filename]

    path = get_model_path(filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model not found: {path}"
        )

    model = joblib.load(path)

    _model_cache[filename] = model

    return model


# ==========================================================
# Scaler
# ==========================================================

def save_scaler(scaler):
    save_model(scaler, "scaler.pkl")


def load_scaler():
    return load_model("scaler.pkl")


# ==========================================================
# Isolation Forest
# ==========================================================

def save_isolation_forest(model):
    save_model(model, "isolation_forest.pkl")


def load_isolation_forest():
    return load_model("isolation_forest.pkl")


# ==========================================================
# XGBoost
# ==========================================================

def save_xgboost(model):
    save_model(model, "xgboost.pkl")


def load_xgboost():
    return load_model("xgboost.pkl")


# ==========================================================
# Utilities
# ==========================================================

def models_exist():
    """
    Check whether all required models exist.
    """

    required_models = [

        "scaler.pkl",

        "isolation_forest.pkl",

        "xgboost.pkl"

    ]

    return all(

        os.path.exists(get_model_path(model))

        for model in required_models

    )


def clear_cache():
    """
    Clears in-memory model cache.

    Useful after retraining.
    """

    _model_cache.clear()

    print("✓ Model cache cleared.")