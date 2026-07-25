<div align="center">

# 🛡️ CrashGuard AI
### AI-Based System Monitoring & Crash Prediction Platform

*Watching your system's vitals in real time — and predicting failures before they happen.*


</div>

---

## 📌 Overview

Servers and personal machines rarely crash without warning signs — CPU spikes, memory pressure, runaway processes, and disk exhaustion usually build up in the minutes before a failure. Most monitoring tools only tell you what is happening *right now*; they don't tell you what is about to go wrong.

**CrashGuard AI** is a full-stack monitoring platform that continuously collects low-level system telemetry (CPU, memory, disk, network, and process data), engineers time-windowed statistical features from that telemetry, and feeds them into two machine learning models — an **Isolation Forest** for unsupervised anomaly detection and an **XGBoost classifier** trained to estimate the probability of a crash in the near future. The result is a live dashboard that doesn't just show system health, it surfaces an early-warning **Crash Risk Score** and actionable cleanup recommendations, so problems can be caught before they turn into downtime.

---

## ✨ Features

- **Real-time system monitoring** — live CPU, memory, disk, and network telemetry served through a Flask API and refreshed on the dashboard
- **Per-resource collectors** that run independently and persist detailed metrics to both PostgreSQL and JSON snapshot files:
  - CPU usage, per-core load, frequency, context switches/interrupts (`cpu_collector.py`)
  - Memory & swap usage, cached/buffer breakdown (`memory_collector.py`)
  - Disk usage, read/write I/O rates, per-partition stats (`disk_collector.py`)
  - Network throughput, per-interface stats, packet/error counts (`network_collector.py`)
  - Process-level monitoring — running/sleeping/zombie counts, thread counts, per-process CPU/memory/I/O (`process_collector.py`)
  - One-time static host info — OS, architecture, CPU model, disk devices, network interfaces (`static_collector.py`, `system_info_collector.py`)
- **PostgreSQL-backed data pipeline** with dedicated tables for raw metrics, runtime info, engineered features, and labeled training windows (`database.sql`)
- **Automated feature engineering**
  - `feature_builder.py` continuously snapshots the latest metrics from every collector into a unified feature row
  - `window_builder.py` rolls those snapshots into 60-sample statistical windows (mean, max, min, std, range, variance, linear trend) per resource
  - `label_windows.py` back-labels windows as crash-precursors based on recorded crash events
- **Crash risk prediction (ML pipeline)**
  - `train_model.py` trains a `StandardScaler`, an `IsolationForest` anomaly detector, and an `XGBoost` binary classifier on the labeled feature windows
  - `risk_predictor.py` loads the trained models and produces a live crash probability, risk level, confidence score, and anomaly flag
  - `anomaly_detector.py` runs a standalone real-time Isolation Forest anomaly-scoring loop against the latest feature row
- **Rule-based alerting** — `alert_manager.py` converts model output into NORMAL / WARNING / CRITICAL alerts with human-readable recommendations, using configurable thresholds
- **Live web dashboard** (`app.py` + `templates/dashboard.html`) — a Flask app with a multi-tab UI (Overview, CPU, Memory, Disk, Network, Processes, Cleanup) that polls `/api/metrics` and renders Chart.js graphs
- **Heuristic crash-risk score on the dashboard** — a live weighted score (`CPU×0.35 + RAM×0.40 + Swap×0.15 + Disk×0.10`) computed directly in the Flask route for instant visual feedback, alongside the trained-model prediction pipeline
- **Actionable cleanup suggestions** — the dashboard surfaces heavy browser processes and stale cache/trash directories that are safe to clear when memory or disk pressure is high
- **Dataset export** — `export_dataset.py` exports labeled feature windows to `dataset.csv` for offline experimentation and retraining

> Only features that exist in the codebase are listed above.

---

## 🏗️ System Architecture

```
                        System Hardware / OS
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │           Metric Collectors (psutil)        │
        │  cpu_collector · memory_collector            │
        │  disk_collector · network_collector          │
        │  process_collector · static_collector        │
        └───────────────────────────────────────────┘
                                │  writes rows + JSON snapshots
                                ▼
                    PostgreSQL Database
        (cpu_metrics, memory_metrics, disk_metrics,
         network_metrics, system_runtime_info, hosts...)
                                │
                                ▼
                    Feature Builder / Scheduler
              (feature_builder.py, feature_scheduler.py)
                                │
                                ▼
                  model_training_features table
                                │
                                ▼
                       Window Builder
                     (window_builder.py)
           60-sample rolling statistical windows
              (avg, max, min, std, trend, range)
                                │
                                ▼
              system_feature_windows table
                     │                    │
                     ▼                    ▼
             Window Labeling        Dataset Export
           (label_windows.py)     (export_dataset.py)
                     │                    │
                     └────────┬───────────┘
                               ▼
                       Model Training
                       (train_model.py)
              StandardScaler → IsolationForest
                          └→ XGBoost Classifier
                               │
                               ▼
                    Risk Predictor / Anomaly Detector
           (risk_predictor.py, anomaly_detector.py)
             Crash Probability · Risk Level · Anomaly Score
                               │
                               ▼
                       Alert Manager
                     (alert_manager.py)
              NORMAL / WARNING / CRITICAL + Recommendation
                               │
                               ▼
              Flask Dashboard (app.py + Chart.js UI)
        Live metrics · Crash risk gauge · Cleanup tips
```

---

## 🧰 Technology Stack

| Category                | Technologies Used |
|--------------------------|--------------------|
| **Language**             | Python 3.13 |
| **Backend / API**        | Flask |
| **Frontend**             | HTML5, CSS3, JavaScript, [Chart.js](https://www.chartjs.org/), Font Awesome |
| **Database**             | PostgreSQL (via `psycopg2`) |
| **Data Processing**      | pandas, NumPy, SciPy (`linregress` for trend features) |
| **Machine Learning**     | scikit-learn (`IsolationForest`, `StandardScaler`), XGBoost (`XGBClassifier`) |
| **Model Persistence**    | joblib |
| **System Monitoring**    | psutil |
| **Environment / Tooling**| Python `venv`, pip |

---

## 📁 Project Structure

```
ai-based-system-monitoring/
│
├── app.py                        # Flask app: dashboard route + /api/metrics live telemetry endpoint
├── config.py                     # DB config, feature column list, model paths, alert thresholds
├── db.py                         # PostgreSQL connection + query execution helpers
│
├── static_collector.py           # One-time host/CPU/disk/network hardware inventory
├── system_info_collector.py      # Snapshot of OS/CPU/memory/disk info to JSON
├── cpu_collector.py               # Continuous CPU metrics collector
├── memory_collector.py           # Continuous memory/swap metrics collector
├── disk_collector.py             # Continuous disk usage + I/O rate collector
├── network_collector.py          # Continuous network throughput collector
├── process_collector.py          # Continuous process/thread state collector
│
├── feature_builder.py            # Merges latest per-resource metrics into one feature row
├── feature_scheduler.py          # Runs feature_builder.py on a fixed interval
├── window_builder.py             # Builds rolling statistical windows for ML input
├── label_windows.py              # Labels windows as crash-precursors from crash events
├── export_dataset.py             # Exports labeled windows to dataset.csv
│
├── train_model.py                # Trains StandardScaler, IsolationForest, and XGBoost
├── model_utils.py                # Save/load helpers + in-memory cache for trained models
├── risk_predictor.py             # Loads models and computes live crash-risk predictions
├── anomaly_detector.py           # Standalone real-time anomaly-scoring loop
├── alert_manager.py              # Converts predictions into NORMAL/WARNING/CRITICAL alerts
│
├── models/                       # Persisted trained models
│   ├── scaler.pkl
│   ├── isolation_forest.pkl
│   └── xgboost.pkl
│
├── database.sql                  # PostgreSQL schema (all tables + indexes)
├── dataset.csv                   # Exported labeled feature-window dataset (340 rows)
│
├── *_detailed_metrics.json       # Latest snapshot written by each collector (CPU/mem/disk/network/process)
├── system_static_info.json       # Latest static host info snapshot
├── anomaly_results.json          # Latest anomaly-detector output
│
├── templates/
│   └── dashboard.html            # Multi-tab dashboard UI (Overview/CPU/Memory/Disk/Network/Processes/Cleanup)
│
├── static/
│   ├── css/style.css             # Dashboard styling
│   ├── js/app.js                 # Fetches /api/metrics, updates cards & cleanup suggestions
│   ├── js/charts.js              # Chart.js graph setup
│   └── images/                   # Logo/background assets
│
├── requirements.txt
└── README.md
```

---

## ⚙️ How It Works

1. **Collection** — Each `*_collector.py` script runs in its own loop (interval defined per collector, typically 1–3 seconds), reading live metrics via `psutil` and writing them both to a JSON snapshot file (used for quick debugging) and to a dedicated PostgreSQL table (`cpu_metrics`, `memory_metrics`, `disk_metrics`, `network_metrics`, `system_runtime_info`).
2. **Feature snapshotting** — `feature_scheduler.py` repeatedly calls `feature_builder.py`, which pulls the *latest* row from each metrics table and merges them into a single row in `model_training_features` — one consolidated view of system state at a point in time.
3. **Windowing** — `window_builder.py` pulls the most recent 60 feature rows, computes rolling statistics (mean, max, min, standard deviation, range, variance, and linear trend via `scipy.stats.linregress`) for CPU, memory, disk, network, and process metrics, and stores the result as a single row in `system_feature_windows`. This turns raw point-in-time metrics into the kind of trend-aware features an ML model can learn from.
4. **Labeling** — `label_windows.py` looks at recorded `system_events` (crash/manual-test-crash entries) and retroactively labels any feature window that falls within a configurable time horizon (default 5 minutes) *before* a crash as a positive (`crash_label = 1`) example.
5. **Learning** — `train_model.py` loads the labeled windows, fits a `StandardScaler`, trains an `IsolationForest` (unsupervised, for anomaly scoring) and an `XGBClassifier` (supervised, for crash probability), and persists all three artifacts with `model_utils.py`.
6. **Prediction** — `risk_predictor.py` loads the trained models, pulls the most recent feature window, scales it, and returns a crash probability, a discrete risk level (LOW/MEDIUM/HIGH/CRITICAL), a confidence score, and an Isolation Forest anomaly flag/score.
7. **Alerting** — `alert_manager.py` wraps the predictor output in threshold logic (`WARNING_THRESHOLD` / `CRITICAL_THRESHOLD` from `config.py`) to produce a plain-language alert level, message, and recommended action.
8. **Visualization** — `app.py` serves a Flask dashboard that polls live telemetry through `/api/metrics` (with its own lightweight, dependency-free weighted crash-risk formula for instant display) and renders it with Chart.js, alongside process lists and automatically generated cleanup suggestions (heavy browser processes, full disks, stale caches/trash).

---

## 🤖 Machine Learning Pipeline

| Stage | Details |
|---|---|
| **Dataset generation** | Built from real collected telemetry, rolled into 60-sample statistical windows and labeled by proximity to recorded crash events (`label_windows.py`) |
| **Feature engineering** | 29 engineered features per window — average/max/min/std/range/variance/trend for CPU, memory, disk, and process metrics, plus average/std for network in/out, and process/thread averages (full list in `config.py → FEATURE_COLUMNS`) |
| **Preprocessing** | `StandardScaler` fit on the training features and reused at inference time |
| **Models trained** | 1) `IsolationForest` (300 estimators, 2% contamination) for unsupervised anomaly detection 2) `XGBClassifier` (300 estimators, max depth 5, learning rate 0.05) for supervised crash-probability prediction, with `scale_pos_weight` computed automatically to handle class imbalance |
| **Prediction output** | Crash probability (0–1), discrete risk level (LOW/MEDIUM/HIGH/CRITICAL), prediction confidence, Isolation Forest anomaly score and anomaly flag |
| **Evaluation** | `train_model.py` prints a classification report, confusion matrix, ROC-AUC score, and the top 15 most important features after each training run |
| **Current dataset stage** | The exported `dataset.csv` contains 340 labeled windows (277 negative / 63 positive) — enough to train and evaluate the pipeline end-to-end, but small by production ML standards. Collecting more data over longer monitoring periods (and across more crash events) will improve model generalization. |

---

## 🚀 Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/ai-based-system-monitoring.git
cd ai-based-system-monitoring
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv aibsv
source aibsv/bin/activate      # On Windows: aibsv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install flask psutil psycopg2-binary pandas numpy scipy scikit-learn xgboost joblib
```
> `requirements.txt` currently pins `numpy` and `wheel`; the additional packages above are imported throughout the codebase (Flask, psutil, psycopg2, pandas, scipy, scikit-learn, xgboost, joblib) and are needed to run all components. Consider regenerating `requirements.txt` with `pip freeze` once your environment is set up.

### 4. Set up PostgreSQL
Create the database and apply the schema:
```bash
createdb system_monitoring
psql -d system_monitoring -f database.sql
```

### 5. Configure database credentials
Update the `DB_CONFIG` dictionary in `config.py` with your local PostgreSQL host, port, database name, username, and password. For a public/shared repository, it's recommended to move these into environment variables rather than committing them directly.

### 6. Collect static host information (run once)
```bash
python3 static_collector.py
python3 system_info_collector.py
```

### 7. Start the runtime collectors
Run each collector in its own terminal/process (or manage them with a process supervisor):
```bash
python3 cpu_collector.py
python3 memory_collector.py
python3 disk_collector.py
python3 network_collector.py
python3 process_collector.py
```

### 8. Start feature engineering
```bash
python3 feature_scheduler.py   # continuously builds model_training_features rows
python3 window_builder.py      # continuously builds system_feature_windows rows
```

### 9. (Optional) Label windows and export a training dataset
```bash
python3 label_windows.py
python3 export_dataset.py
```

### 10. Train the models
```bash
python3 train_model.py
```
This produces `models/scaler.pkl`, `models/isolation_forest.pkl`, and `models/xgboost.pkl`.

### 11. Run the dashboard
```bash
python3 app.py
```
Then open **http://127.0.0.1:5001** in your browser.

---

## ▶️ Usage

1. **Start monitoring** — Launch the collectors and the feature pipeline (steps 7–8 above) so the system continuously ingests fresh telemetry.
2. **View the dashboard** — Run `python3 app.py` and open the browser to see live CPU, memory, disk, network, and process stats update automatically, along with a live weighted crash-risk score.
3. **Get crash predictions** — Once models are trained, run `python3 risk_predictor.py` (or integrate `RiskPredictor` into a service) to get the ML-based crash probability, risk level, and anomaly flag for the latest feature window.
4. **Check alerts** — Run `python3 alert_manager.py` to see the current alert level (NORMAL / WARNING / CRITICAL) with a human-readable message and recommended action.
5. **Interpret results**:
   - **Risk level LOW/NORMAL** — system operating within normal bounds.
   - **MEDIUM/WARNING** — resource strain increasing; monitor closely.
   - **HIGH/CRITICAL** — crash risk is elevated; investigate CPU, memory, and disk usage immediately, and consider acting on the dashboard's cleanup suggestions.

---

## 📸 Screenshots

> Add real screenshots here once available.

![Dashboard Overview](images/dashboard.png)
![System Metrics Visualization](images/metrics.png)
![Crash Prediction Result](images/prediction.png)

---

## 📊 Results / Performance

`train_model.py` automatically prints the following after every training run:
- Classification report (precision/recall/F1 for crash vs. non-crash windows)
- Confusion matrix
- ROC-AUC score
- Top 15 most important features by XGBoost feature importance

The current `dataset.csv` snapshot contains 340 labeled windows (277 negative, 63 positive). Run `python3 train_model.py` against a fresh export to generate up-to-date metrics for your own dataset, and paste the console output (or a screenshot of it) into this section for your portfolio.

---

## 🔭 Future Improvements

- Move to a FastAPI backend with WebSocket-based live updates instead of polling
- Containerize the full stack with Docker Compose (Flask app + PostgreSQL + collectors)
- Add multi-host monitoring support (the schema already models `host_id`)
- Explore deep learning approaches (e.g., LSTM/temporal models) for sequence-aware crash prediction
- Integrate with Prometheus/Grafana for production-grade observability
- Add email/SMS/webhook-based alert delivery instead of console output
- Automate periodic model retraining as new labeled data accumulates
- Expand the labeled dataset with more real crash events for better generalization
- Add authentication to the dashboard before any external deployment

---

## 👩‍💻 Author

**Siddhi Jain**
B.Tech, Computer Science Engineering (AI & ML)
UPES, Dehradun

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Siddhi Jain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```