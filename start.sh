#!/usr/bin/env bash
# ==========================================================
# CrashGuard AI - Local Startup Script
# ==========================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "🛡️  CrashGuard AI - System Monitoring Platform"
echo "=========================================================="

# 1. Check Python virtual environment
if [ -d "./.venv" ]; then
    PYTHON_EXEC="./.venv/bin/python"
    echo "✓ Using virtual environment: ./.venv"
elif [ -d "./venv" ]; then
    PYTHON_EXEC="./venv/bin/python"
    echo "✓ Using virtual environment: ./venv"
elif [ -d "./aibsv" ]; then
    PYTHON_EXEC="./aibsv/bin/python"
    echo "✓ Using virtual environment: ./aibsv"
else
    PYTHON_EXEC="python3"
    echo "⚠️ Virtual environment not found, falling back to system python3"
fi

# 2. Check trained models
if [ ! -f "models/xgboost.pkl" ] || [ ! -f "models/scaler.pkl" ]; then
    echo "⏳ Training models on dataset.csv..."
    "$PYTHON_EXEC" train_model.py
else
    echo "✓ ML models found in models/ (StandardScaler, IsolationForest, XGBoost)"
fi

# 3. Launch Flask Dashboard
PORT="${PORT:-5001}"
echo "=========================================================="
echo "🚀 Starting CrashGuard AI Web Dashboard on http://localhost:${PORT}"
echo "=========================================================="
export PORT
exec "$PYTHON_EXEC" app.py
