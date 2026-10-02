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
├── core/                         # Core configurations & shared database utilities
│   ├── config.py                 # Centralized configuration & alert thresholds
│   └── db.py                     # PostgreSQL connection management & helpers
│
├── collectors/                   # Low-level system telemetry collectors (psutil)
│   ├── cpu_collector.py          # Continuous CPU metrics collector
│   ├── memory_collector.py       # Continuous memory/swap metrics collector
│   ├── disk_collector.py         # Continuous disk usage + I/O rate collector
│   ├── network_collector.py      # Continuous network throughput collector
│   ├── process_collector.py      # Continuous process/thread state collector
│   ├── static_collector.py       # One-time host/hardware inventory to PostgreSQL
│   └── system_info_collector.py  # Static host info snapshot
│
├── pipeline/                     # Data engineering & rolling feature windows
│   ├── feature_builder.py        # Merges latest per-resource metrics into one feature row
│   ├── feature_scheduler.py      # Runs feature_builder.py on a fixed interval
│   ├── window_builder.py         # Builds rolling statistical windows (60 samples)
│   ├── label_windows.py          # Labels windows as crash-precursors from crash events
│   └── export_dataset.py         # Exports labeled windows to data/dataset.csv
│
├── ml/                           # Machine learning models, training & inference
│   ├── train_model.py            # Trains StandardScaler, IsolationForest, and XGBoost
│   ├── model_utils.py            # Save/load helpers & in-memory cache for models
│   ├── risk_predictor.py         # Live crash-risk & anomaly prediction engine
│   ├── anomaly_detector.py       # Standalone real-time Isolation Forest scoring loop
│   └── alert_manager.py          # Rule-based NORMAL/WARNING/CRITICAL alert generator
│
├── web/                          # Full-stack web dashboard & API
│   ├── app.py                    # Flask application serving dashboard & live ML API
│   ├── templates/
│   │   └── dashboard.html        # Multi-tab dashboard UI
│   └── static/
│       ├── css/style.css         # Dashboard styling
│       └── js/app.js, charts.js  # Frontend telemetry fetcher & Chart.js renderer
│
├── stress_tests/                 # Controlled system stress & crash simulation scripts
│   ├── cpu_stress.py             # CPU saturation test
│   ├── memory_stress.py          # Memory leak simulator
│   ├── disk_stress.py            # Disk exhaustion simulator
│   ├── process_stress.py         # Fork-bomb process simulator
│   └── thread_stress.py          # Thread exhaustion simulator
│
├── scripts/                      # Offline dataset expansion & physical telemetry tools
│   ├── collect_live_physical_data.py
│   ├── expand_real_dataset.py
│   ├── apply_realistic_system_dynamics.py
│   ├── restore_and_label_real_dataset.py
│   └── run_live_data_campaign.py
│
├── models/                       # Persisted trained model artifacts (.pkl)
│   ├── scaler.pkl
│   ├── isolation_forest.pkl
│   └── xgboost.pkl
│
├── data/                         # Datasets, schemas & runtime cache
│   ├── dataset.csv               # Cleaned & labeled feature-window dataset
│   ├── database.sql              # PostgreSQL schema (tables & indexes)
│   └── runtime/                  # Ephemeral metrics snapshots (*.json)
│
├── app.py                        # Root launcher forwarding to web/app.py
├── train_model.py                # Root launcher forwarding to ml/train_model.py
├── start.sh                      # Local startup script
├── Dockerfile                    # Containerization specification
├── docker-compose.yml            # Multi-container orchestration (App + PostgreSQL)
├── requirements.txt              # Python package dependencies
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
| **Models trained** | 1) `IsolationForest` (200 estimators, 8% contamination) for unsupervised anomaly detection 2) `XGBClassifier` (150 estimators, max depth 4, learning rate 0.06, subsample 0.8, colsample_bytree 0.8) for supervised crash-probability prediction, with `scale_pos_weight = clamp(0.45 × neg/pos, 1.5, 4.0)` to handle class imbalance (3.23 on the current dataset) |
| **Prediction output** | Crash probability (0–1), discrete risk level (LOW/MEDIUM/HIGH/CRITICAL), a margin score `|p − 0.5| × 2` (not a calibrated confidence), Isolation Forest anomaly score and anomaly flag |
| **Current dataset stage** | **51,262 feature windows** (45,106 normal / 6,156 stress precursors, 12.0% positive) in `data/dataset.csv`. Built from ~17K windows of real `psutil` telemetry recorded on a Mac during labeled sessions (idle, multitasking, CPU starvation, memory pressure, thread storms), then **augmented**: 3× linear interpolation (`scripts/expand_real_dataset.py`), 2% Gaussian sensor jitter, and random label flips to model boundary ambiguity (`scripts/apply_realistic_system_dynamics.py`). |

---

## 🚀 Installation and Setup

### ⚡ Option A: One-Command Docker Deployment (Recommended)
Run the entire stack — PostgreSQL database, schema initialization, ML models, and live web dashboard — in isolated containers:
```bash
docker compose up --build -d
```
Then open **http://localhost:5000** in your browser. To view logs or stop:
```bash
docker compose logs -f app
docker compose down
```

---

### 💻 Option B: One-Click Local Setup
If you prefer running natively on your host machine:
```bash
chmod +x start.sh
./start.sh
```
This automatically selects your virtual environment (`.venv`, `venv`, or `aibsv`), trains models if they are missing, and starts the dashboard on **http://localhost:5001** (override with `PORT`).

---

### 🛠️ Option C: Manual Step-by-Step Setup

#### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/ai-based-system-monitoring.git
cd ai-based-system-monitoring
```

#### 2. Set up virtual environment and install dependencies
```bash
python3 -m venv aibsv
source aibsv/bin/activate      # On Windows: aibsv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Set up PostgreSQL (Optional if training offline on dataset.csv)
```bash
createdb system_monitoring
psql -d system_monitoring -f database.sql
```
Credentials can be configured via environment variables (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) or edited in `config.py`.

#### 4. Train the ML models
```bash
python3 train_model.py
```
Trains the `StandardScaler`, `IsolationForest`, and `XGBClassifier` and saves model artifacts to `models/`. The script reads `system_feature_windows` from PostgreSQL if it is reachable and only falls back to `data/dataset.csv` (51,262 windows) when the database is unavailable. To train on the CSV while Postgres is running, point the connection elsewhere, e.g. `DB_PORT=1 python3 train_model.py`.

#### 5. Launch the Dashboard
```bash
python3 app.py
```
Open **http://localhost:5001** to view live system vitals, the blended crash-risk score, and process inspection.

---

### 🔴 Live Hardware Telemetry Collection
To stream brand new live physical sensor measurements directly into `dataset.csv`:
```bash
# Interactive guided campaign (idle, multitasking, CPU burn, memory leaks, thread storms):
python3 run_live_data_campaign.py

# Or background streaming during everyday use:
python3 collect_live_physical_data.py --step 2 --label 0 --tag "daily_work"
```

---

## ▶️ Usage

1. **Start monitoring** — Launch `app.py` or run `docker compose up -d` to view real-time telemetry.
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

## 📊 Model Evaluation & Benchmark Performance

Reproduced on 2026-10-02 by running `python3 train_model.py` against `data/dataset.csv` (51,262 windows). Evaluated on the last **10,253 windows** using a positional **80/20 split** of the time-ordered CSV (the scaler is fit on the training portion only):

### 1. Test Set Classification Report
```
              precision    recall  f1-score   support

     Normal       0.97      0.93      0.95      9116
 Crash Risk       0.57      0.75      0.65      1137

   accuracy                           0.91     10253
  macro avg       0.77      0.84      0.80     10253
weighted avg       0.92      0.91      0.92     10253
```

- **Crash-class recall**: **0.75** (858 of 1,137 stress-precursor windows caught)
- **Crash-class precision**: **0.57** (640 false alarms)
- **Test ROC-AUC**: **0.9426**
- **Accuracy**: 0.91. Note that predicting "normal" for every window would already score ~0.89 on this test set, so recall, precision and AUC are the meaningful numbers.
- **Confusion Matrix**: TN **8,476** · FP **640** · FN **279** · TP **858**

### 2. Caveats
- **Labels are stress-session labels, not recorded crashes.** A positive means "a window recorded during a CPU, memory or thread stress session"; no actual system crash was captured.
- **Augmentation affects the evaluation.** Interpolated rows are blends of their neighbours, and consecutive windows share up to 58 of 60 samples, so rows near the train/test boundary are not fully independent. The random label flips added for ambiguity also put a ceiling on achievable precision and recall.
- **Raw database pipeline results are much weaker.** Training the same configuration on the 17,285 windows collected through the PostgreSQL pipeline (only 97 positives) gives ROC-AUC 0.82 and catches 0 of 34 test positives; that path needs far more labeled positive data.
- **Thresholds are not tuned or calibrated.** The report uses XGBoost's default 0.5 cut-off, and `scale_pos_weight` shifts probabilities upward.

### 3. Top Features Learned by XGBoost (gain-based `feature_importances_`)
1. `cpu_max` (**24.0%**): pinned runaway loops and core starvation
2. `thread_avg` (**14.5%**): thread-storm sessions
3. `memory_max` (**13.3%**): RAM ceiling saturation
4. `running_process_avg` (**8.2%**): run-queue pressure
5. `memory_trend` (**7.8%**): upward memory slope during leaks

---

## 🧠 Systems Engineering Deep-Dive (Production Scale & Design)

### 1. Eliminating Target Leakage (The Data Engineering Challenge)
In early iterations, labels were defined via deterministic threshold rules (e.g. `cpu_max >= 75%`). Because those same features were fed into XGBoost, the model trivialized the problem to an artificial `0.9999` ROC-AUC by memorizing threshold cut-offs.  
**Fix:** Labels were decoupled from feature formulas and assigned per recorded stress session (`scripts/run_live_data_campaign.py --label`), so the model can no longer read the label straight off a threshold. On the current dataset this gives the **0.9426 ROC-AUC** reported above.

### 2. Low-Overhead Telemetry
- **Bounded in-memory window**: the dashboard keeps the last 60 samples in a `collections.deque(maxlen=60)` (O(1) append with automatic eviction), so live feature computation needs no database round trip.
- **Decoupled sampling (dataset collector)**: `scripts/collect_live_physical_data.py` samples every 1 s and emits a window every 2 s.
- Inference currently runs synchronously inside the `/api/metrics` request; moving sampling and inference to a background worker is on the roadmap.

### 3. Proposed Scale-Out Architecture (design only, not implemented)
To move from single-node monitoring to a distributed fleet:

```
[Host Agent 1] (psutil collector) ──┐
[Host Agent 2] (psutil collector) ──┼──> [Apache Kafka / Redis Stream]
[Host Agent N] (psutil collector) ──┘                  │
                                                       ▼
                                         [Stream Workers (Flink / Celery)]
                                         (60-step sliding window calculation)
                                                       │
                                       ┌───────────────┴───────────────┐
                                       ▼                               ▼
                           [TimescaleDB / InfluxDB]        [Inference Service (Triton)]
                           (Partitioned Time-Series)       (batched XGBoost scoring)
                                       │                               │
                                       └───────────────┬───────────────┘
                                                       ▼
                                         [Alert Manager & Grafana/UI]
```

---

## 💼 Fresher SDE Interview Cheat Sheet (20+ LPA Preparation)

Use these concrete talking points when presenting CrashGuard AI to Tier-1 interviewers:

1. **How do you handle class imbalance in system monitoring?**
   > *"Stress precursors are 12% of the windows. I up-weight the positive class with a clamped `scale_pos_weight = clamp(0.45 × negative / positive, 1.5, 4.0)` (3.23 here), evaluate on recall, precision and ROC-AUC instead of accuracy, and use a time-ordered split rather than a random one."*
2. **Why XGBoost over an LSTM or Deep Learning?**
   > *"The inputs are 29 tabular aggregates of a 60-sample window (trend, variance, max, min), and the dataset is small. Gradient-boosted trees fit that shape well, train in seconds on a CPU, need no GPU, and expose feature importance, which matters for explaining an alert."*
3. **What was your biggest engineering challenge on this project?**
   > *"Diagnosing and resolving target leakage. Initial models appeared to have near-perfect accuracy because labels were generated via deterministic rule thresholds. I restructured the data campaign to ground labels on independent physical workload experiments, ensuring the model learned true causal failure indicators."*

---

## 🔭 Future Roadmap

- Move from HTTP polling to WebSocket-based live server-sent updates (FastAPI backend).
- Stream ingestion through Apache Kafka for distributed multi-cluster deployments.
- Auto-remediation sidecars (e.g. automatically clearing caches or renicing rogue PIDs when Risk Score exceeds 80%).
- Integration with Prometheus metrics exporter format.

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