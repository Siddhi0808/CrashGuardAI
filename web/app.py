"""
CrashGuard AI web dashboard and live-telemetry API.

Routes:
    GET /             -> dashboard page (templates/dashboard.html)
    GET /api/metrics  -> live CPU/memory/disk/network/process snapshot, a blended
                         crash-risk score, and the ML prediction (or null)

Each /api/metrics call reads psutil directly (not the database), appends one
sample to an in-memory 60-sample window, and runs the trained models on
features computed from that window.
"""

import sys, os

# Make the project root importable when this file is run directly
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import platform
import threading
from collections import deque
import numpy as np
import pandas as pd
from scipy.stats import linregress
import psutil
from flask import Flask, render_template, jsonify

try:
    from ml.risk_predictor import predictor
    from core.config import FEATURE_COLUMNS
except ImportError:
    from risk_predictor import predictor
    from config import FEATURE_COLUMNS

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(WEB_DIR, "templates")
STATIC_DIR = os.path.join(WEB_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# In-memory buffer for real-time statistical window feature calculations
LIVE_BUFFER = deque(maxlen=60)
# Flask serves requests on multiple threads; guard appends and snapshots of the buffer
LIVE_BUFFER_LOCK = threading.Lock()


def compute_live_features_from_buffer(buf):
    """
    Turn the recent raw samples into the 29 model features (see FEATURE_COLUMNS).

    Args:
        buf: sequence of sample dicts with keys cpu, memory, disk, net_in,
             net_out, procs, running, threads (oldest first).

    Returns:
        dict of feature name -> float, or None when fewer than 10 samples exist.
        The formulas match scripts/collect_live_physical_data.py, but note the
        training windows were 60 samples taken 1 s apart, while this buffer gets
        one sample per dashboard poll.
    """
    if len(buf) < 10:
        return None

    def calc_stats(series):
        """Return (mean, max, min, std, trend, range, variance) for one metric."""
        s = pd.Series(series)
        avg = float(s.mean())
        s_max = float(s.max())
        s_min = float(s.min())
        std = float(s.std(ddof=1)) if len(s) > 1 else 0.0
        var = float(s.var(ddof=1)) if len(s) > 1 else 0.0
        s_range = float(s_max - s_min)
        # Trend = slope of a least-squares line through the samples
        # (change per sample; positive means the metric is rising)
        if len(s) >= 2:
            x = np.arange(len(s))
            slope, _, _, _, _ = linregress(x, s.values)
            trend = float(slope) if not np.isnan(slope) else 0.0
        else:
            trend = 0.0
        return avg, s_max, s_min, std, trend, s_range, var

    # Split the samples into one series per metric
    cpu_s = [b['cpu'] for b in buf]
    mem_s = [b['memory'] for b in buf]
    disk_s = [b['disk'] for b in buf]
    net_in_s = [b['net_in'] for b in buf]
    net_out_s = [b['net_out'] for b in buf]
    proc_s = [b['procs'] for b in buf]
    run_s = [b['running'] for b in buf]
    th_s = [b['threads'] for b in buf]

    c_avg, c_max, c_min, c_std, c_trend, c_range, c_var = calc_stats(cpu_s)
    m_avg, m_max, m_min, m_std, m_trend, m_range, _ = calc_stats(mem_s)
    d_avg, d_max, d_min, d_std, d_trend, d_range, _ = calc_stats(disk_s)

    # Network values are cumulative byte counters since boot (same as the training data)
    n_in_avg = float(np.mean(net_in_s))
    n_out_avg = float(np.mean(net_out_s))
    n_in_std = float(np.std(net_in_s, ddof=1)) if len(net_in_s) > 1 else 0.0
    n_out_std = float(np.std(net_out_s, ddof=1)) if len(net_out_s) > 1 else 0.0

    p_avg, p_max, p_min, p_std, _, _, _ = calc_stats(proc_s)
    run_avg = float(np.mean(run_s))
    th_avg = float(np.mean(th_s))

    return {
        "cpu_avg": c_avg, "cpu_max": c_max, "cpu_min": c_min,
        "cpu_std": c_std, "cpu_trend": c_trend, "cpu_range": c_range, "cpu_variance": c_var,

        "memory_avg": m_avg, "memory_max": m_max, "memory_min": m_min,
        "memory_std": m_std, "memory_range": m_range, "memory_trend": m_trend,

        "disk_avg": d_avg, "disk_max": d_max, "disk_min": d_min,
        "disk_std": d_std, "disk_range": d_range, "disk_trend": d_trend,

        "network_in_avg": n_in_avg, "network_out_avg": n_out_avg,
        "network_in_std": n_in_std, "network_out_std": n_out_std,

        "process_avg": p_avg, "process_max": p_max, "process_min": p_min, "process_std": p_std,
        "running_process_avg": run_avg, "thread_avg": th_avg
    }


@app.route('/')
def dashboard():
    """Serve the single-page dashboard; all live data is fetched from /api/metrics."""
    return render_template('dashboard.html')


@app.route('/api/metrics')
def get_metrics():
    """
    Return a live system snapshot as JSON (polled by static/js/app.js every 2 s).

    Steps: read psutil -> heuristic risk score -> scan processes -> add a sample
    to the live buffer -> ML prediction (if models are loaded) -> cleanup tips.
    """
    # 1. Gather Telemetry
    # interval=None is non-blocking: CPU % since the previous call (0.0 on the very first call)
    cpu_pct = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/' if os.name != 'nt' else 'C:\\')
    net = psutil.net_io_counters()

    # 2. Heuristic Crash Risk Formula
    # Hand-picked weights (sum to 1.0) so the dashboard has a score even without trained models
    heuristic_score = min(100.0, round(
        (cpu_pct * 0.35) +
        (vm.percent * 0.40) +
        (swap.percent * 0.15) +
        (disk.percent * 0.10), 1
    ))

    # 3. Active & Sleeping Processes Inspection
    all_processes = []
    browser_tabs_suggestions = []

    known_browsers = {
        'chrome': ('Google Chrome', 'fa-chrome'),
        'safari': ('Safari Browser', 'fa-safari'),
        'firefox': ('Firefox Browser', 'fa-firefox'),
        'msedge': ('Microsoft Edge', 'fa-edge'),
        'brave': ('Brave Browser', 'fa-compass'),
        'arc': ('Arc Browser', 'fa-compass')
    }

    running_count = 0
    total_threads = 0

    # Passing the attribute list lets psutil fetch them in one pass per process
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'memory_info', 'num_threads']):
        try:
            pinfo = proc.info
            name = pinfo['name'] or ''
            status = pinfo['status'] or 'unknown'
            mem_mb = round((pinfo['memory_info'].rss if pinfo['memory_info'] else 0) / (1024 ** 2), 1)
            mem_pct = pinfo['memory_percent'] or 0.0
            cpu_p = pinfo['cpu_percent'] or 0.0
            num_th = pinfo.get('num_threads') or 1
            total_threads += num_th

            if status == psutil.STATUS_RUNNING:
                running_count += 1

            all_processes.append({
                'pid': pinfo['pid'],
                'name': name,
                'status': status,
                'cpu_percent': cpu_p,
                'memory_percent': mem_pct,
                'memory_mb': mem_mb
            })

            # Heavy browser tab detection
            name_lower = name.lower()
            for b_key, (b_name, icon_class) in known_browsers.items():
                if b_key in name_lower and (mem_mb > 150 or mem_pct > 3.0):
                    browser_tabs_suggestions.append({
                        'title': f'Close Heavy {b_name} Process/Tab',
                        'description': f'Process "{name}" ({status}) is taking {mem_mb} MB RAM ({mem_pct:.1f}%). Closing it frees system memory.',
                        'impact': f'{mem_mb} MB RAM',
                        'pid': pinfo['pid'],
                        'icon': icon_class,
                        'level': 'critical' if mem_mb > 400 else 'warning'
                    })
                    break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process exited mid-scan or belongs to a protected user; skip it
            pass

    # Top 15 processes by memory share for the Processes tab
    sorted_procs = sorted(all_processes, key=lambda x: x['memory_percent'], reverse=True)[:15]

    # 4. Append to Live Buffer & Calculate ML Prediction
    with LIVE_BUFFER_LOCK:
        LIVE_BUFFER.append({
            'cpu': cpu_pct,
            'memory': vm.percent,
            'disk': disk.percent,
            'net_in': net.bytes_recv,
            'net_out': net.bytes_sent,
            'procs': len(all_processes),
            'running': running_count,
            'threads': total_threads
        })
        buffer_snapshot = list(LIVE_BUFFER)

    ml_prediction = None
    final_risk_score = heuristic_score

    try:
        if predictor.is_ready:
            live_feat = compute_live_features_from_buffer(buffer_snapshot)
            if live_feat is not None:
                ml_prediction = predictor.predict_from_features(live_feat)
                # Final score = 60% model probability + 40% heuristic (both on a 0-100 scale)
                ml_prob_pct = ml_prediction['crash_probability'] * 100.0
                final_risk_score = round(0.6 * ml_prob_pct + 0.4 * heuristic_score, 1)
    except Exception as e:
        app.logger.warning(f'ML prediction failed, using heuristic score only: {e}')

    # 5. Storage & System Cleanup Suggestions (suggestions only; nothing is deleted)
    cleanup_suggestions = []
    if vm.percent > 80:
        cleanup_suggestions.append({
            'title': f'High Memory Pressure ({vm.percent}% RAM Used)',
            'description': 'RAM resources are critically strained. Close sleeping background apps to avoid Out-Of-Memory system panics.',
            'icon': 'fa-memory',
            'level': 'critical'
        })

    if disk.percent > 85:
        cleanup_suggestions.append({
            'title': f'Low Storage Disk Space ({disk.percent}% Full)',
            'description': 'Storage is low, which prevents the OS from creating virtual swap files.',
            'icon': 'fa-hard-drive',
            'level': 'critical'
        })

    # Cross-platform cache directory detection
    current_os = platform.system()
    cache_dirs = []
    if current_os == "Darwin":
        cache_dirs = [
            ("~/Library/Caches", "User App Caches", "Remove temporary application cache files."),
            ("/tmp", "System Temp Folder", "Clear temporary process cache directory."),
            ("~/.Trash", "System Trash Bin", "Empty trash bin to recover storage space.")
        ]
    elif current_os == "Linux":
        cache_dirs = [
            ("~/.cache", "User App Caches", "Remove user application cache files."),
            ("/tmp", "System Temp Folder", "Clear temporary process cache directory."),
            ("~/.local/share/Trash", "System Trash Bin", "Empty trash bin to recover storage space.")
        ]
    elif current_os == "Windows":
        temp_dir = os.environ.get("TEMP", "C:\\Windows\\Temp")
        cache_dirs = [
            (temp_dir, "Windows Temp Folder", "Clear temporary user cache directory.")
        ]

    for path_raw, title, desc in cache_dirs:
        expanded_path = os.path.expanduser(path_raw)
        if os.path.exists(expanded_path):
            cleanup_suggestions.append({
                'title': title,
                'description': desc,
                'path': path_raw,
                'icon': 'fa-folder-minus',
                'level': 'warning' if 'Trash' in title else 'info'
            })

    # 6. Response consumed by static/js/app.js
    return jsonify({
        'cpu': {
            'percent': cpu_pct,
            'cores': psutil.cpu_count(logical=True)
        },
        'memory': {
            'percent': vm.percent,
            'used_gb': round(vm.used / (1024 ** 3), 2),
            'free_gb': round(vm.available / (1024 ** 3), 2),
            'total_gb': round(vm.total / (1024 ** 3), 2),
            'swap_percent': swap.percent
        },
        'disk': {
            'percent': disk.percent,
            'used_gb': round(disk.used / (1024 ** 3), 2),
            'free_gb': round(disk.free / (1024 ** 3), 2),
            'total_gb': round(disk.total / (1024 ** 3), 2)
        },
        'network': {
            # Totals since boot, not per-second rates
            'rx_mb': round(net.bytes_recv / (1024 ** 2), 2),
            'tx_mb': round(net.bytes_sent / (1024 ** 2), 2)
        },
        'crash_risk_score': final_risk_score,
        'ml_prediction': ml_prediction,
        'process_count': len(all_processes),
        'processes': sorted_procs,
        'browser_tab_suggestions': browser_tabs_suggestions[:6],
        'cleanup_suggestions': cleanup_suggestions
    })


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    # Debug mode exposes the Werkzeug debugger; enable only locally with FLASK_DEBUG=1
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host=host, port=port)
