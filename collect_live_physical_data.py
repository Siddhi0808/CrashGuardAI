"""
collect_live_physical_data.py

High-frequency live physical telemetry collector for CrashGuard AI.
Directly samples hardware metrics from psutil every 1 second, computes 60-sample
rolling statistical windows every 2 seconds, and appends genuine live physical
observations directly into dataset.csv.

Usage:
    python collect_live_physical_data.py [--step 2] [--max-rows 10000]
"""

import os
import sys
import time
import argparse
from collections import deque
import psutil
import numpy as np
import pandas as pd
from scipy.stats import linregress
from config import FEATURE_COLUMNS, TARGET_COLUMN

DATASET_FILE = "dataset.csv"
WINDOW_SIZE = 60
DEFAULT_STEP_INTERVAL = 2  # seconds between window computations
SAMPLE_INTERVAL = 1        # seconds between hardware metric readings

def calculate_window_stats(series):
    s = pd.Series(series)
    avg = float(s.mean())
    s_max = float(s.max())
    s_min = float(s.min())
    std = float(s.std(ddof=1)) if len(s) > 1 else 0.0
    if np.isnan(std):
        std = 0.0
    variance = float(s.var(ddof=1)) if len(s) > 1 else 0.0
    if np.isnan(variance):
        variance = 0.0
    s_range = float(s_max - s_min)
    
    x = np.arange(len(s))
    slope, _, _, _, _ = linregress(x, s.values)
    trend = float(slope) if not np.isnan(slope) else 0.0

    return avg, s_max, s_min, std, trend, s_range, variance


def sample_hardware():
    """
    Directly reads physical hardware sensors and kernel statistics via psutil.
    """
    cpu_usage = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    
    # Process and thread counts
    total_procs = 0
    running_procs = 0
    total_threads = 0

    for p in psutil.process_iter(['status', 'num_threads']):
        try:
            total_procs += 1
            info = p.info
            if info.get('num_threads'):
                total_threads += info['num_threads']
            if info.get('status') == psutil.STATUS_RUNNING:
                running_procs += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return {
        'cpu': cpu_usage,
        'memory': vm.percent,
        'disk': disk.percent,
        'net_in': net.bytes_recv,
        'net_out': net.bytes_sent,
        'procs': total_procs,
        'running': running_procs,
        'threads': total_threads
    }


def compute_feature_window(buffer):
    """
    Computes the exact 29 windowed features from 60 physical samples.
    """
    cpu_series = [b['cpu'] for b in buffer]
    mem_series = [b['memory'] for b in buffer]
    disk_series = [b['disk'] for b in buffer]
    net_in_series = [b['net_in'] for b in buffer]
    net_out_series = [b['net_out'] for b in buffer]
    proc_series = [b['procs'] for b in buffer]
    running_series = [b['running'] for b in buffer]
    thread_series = [b['threads'] for b in buffer]

    c_avg, c_max, c_min, c_std, c_trend, c_range, c_var = calculate_window_stats(cpu_series)
    m_avg, m_max, m_min, m_std, m_trend, m_range, _ = calculate_window_stats(mem_series)
    d_avg, d_max, d_min, d_std, d_trend, d_range, _ = calculate_window_stats(disk_series)

    n_in_avg = float(np.mean(net_in_series))
    n_out_avg = float(np.mean(net_out_series))
    n_in_std = float(np.std(net_in_series, ddof=1)) if len(net_in_series) > 1 else 0.0
    n_out_std = float(np.std(net_out_series, ddof=1)) if len(net_out_series) > 1 else 0.0

    p_avg, p_max, p_min, p_std, _, _, _ = calculate_window_stats(proc_series)
    running_avg = float(np.mean(running_series))
    thread_avg = float(np.mean(thread_series))

def compute_feature_window(buffer, forced_label=None):
    """
    Computes the exact 29 windowed features from 60 physical samples.
    If forced_label is provided (0 or 1), it uses the external ground-truth
    label to prevent circular mathematical formula leakage.
    """
    cpu_series = [b['cpu'] for b in buffer]
    mem_series = [b['memory'] for b in buffer]
    disk_series = [b['disk'] for b in buffer]
    net_in_series = [b['net_in'] for b in buffer]
    net_out_series = [b['net_out'] for b in buffer]
    proc_series = [b['procs'] for b in buffer]
    running_series = [b['running'] for b in buffer]
    thread_series = [b['threads'] for b in buffer]

    c_avg, c_max, c_min, c_std, c_trend, c_range, c_var = calculate_window_stats(cpu_series)
    m_avg, m_max, m_min, m_std, m_trend, m_range, _ = calculate_window_stats(mem_series)
    d_avg, d_max, d_min, d_std, d_trend, d_range, _ = calculate_window_stats(disk_series)

    n_in_avg = float(np.mean(net_in_series))
    n_out_avg = float(np.mean(net_out_series))
    n_in_std = float(np.std(net_in_series, ddof=1)) if len(net_in_series) > 1 else 0.0
    n_out_std = float(np.std(net_out_series, ddof=1)) if len(net_out_series) > 1 else 0.0

    p_avg, p_max, p_min, p_std, _, _, _ = calculate_window_stats(proc_series)
    running_avg = float(np.mean(running_series))
    thread_avg = float(np.mean(thread_series))

    if forced_label is not None:
        final_label = int(forced_label)
    else:
        # Fallback automatic physical saturation threshold
        cpu_stress = (c_max >= 80.0) | ((c_avg >= 50.0) & (c_trend > 0))
        mem_stress = (m_max >= 80.0) | ((m_trend > 0.03) & (m_avg > 70.0))
        thread_stress = (thread_avg >= 2600)
        final_label = int(cpu_stress or mem_stress or thread_stress)

    return [
        c_avg, c_max, c_min, c_std, c_trend, c_range, c_var,
        m_avg, m_max, m_min, m_std, m_range, m_trend,
        d_avg, d_max, d_min, d_std, d_range, d_trend,
        n_in_avg, n_out_avg, n_in_std, n_out_std,
        p_avg, p_max, p_min, p_std,
        running_avg, thread_avg,
        final_label
    ]


def start_live_collection(step_interval=DEFAULT_STEP_INTERVAL, max_rows=None, forced_label=None, tag=None):
    print("=" * 65)
    print("CrashGuard AI - Live Hardware Telemetry Collector")
    print("=" * 65)
    print(f"Target file    : {DATASET_FILE}")
    print(f"Window buffer  : {WINDOW_SIZE} physical hardware samples")
    print(f"Sample rate    : Every {SAMPLE_INTERVAL}s")
    print(f"Window step    : Every {step_interval}s (~{int(60/step_interval)} physical rows/min)")
    label_desc = "Auto-Evaluated" if forced_label is None else f"Forced {forced_label} ({'CRASH/STRESS' if forced_label == 1 else 'NORMAL'})"
    print(f"Session label  : {label_desc}")
    if tag:
        print(f"Scenario tag   : {tag}")
    if max_rows:
        print(f"Row limit      : Stop after {max_rows} rows")
    print("=" * 65)

    # Initialize buffer
    buffer = deque(maxlen=WINDOW_SIZE)
    print(f"Warming up buffer with initial {WINDOW_SIZE} physical samples...")
    for i in range(WINDOW_SIZE):
        buffer.append(sample_hardware())
        time.sleep(0.1)

    print(f"✓ Buffer ready ({len(buffer)} physical samples). Starting continuous stream...")

    rows_collected = 0
    last_step_time = time.time()

    try:
        while True:
            time.sleep(SAMPLE_INTERVAL)
            buffer.append(sample_hardware())

            now = time.time()
            if now - last_step_time >= step_interval:
                last_step_time = now
                row = compute_feature_window(buffer, forced_label=forced_label)

                # Append to dataset.csv
                df_row = pd.DataFrame([row], columns=FEATURE_COLUMNS + [TARGET_COLUMN])
                df_row.to_csv(DATASET_FILE, mode='a', header=not os.path.exists(DATASET_FILE), index=False)
                rows_collected += 1

                label_str = "RISK (1)" if row[-1] == 1 else "NORMAL (0)"
                tag_str = f" [{tag}]" if tag else ""
                print(f"[{time.strftime('%H:%M:%S')}] Appended physical row #{rows_collected}{tag_str} | CPU: {row[0]:.1f}% | RAM: {row[7]:.1f}% | Procs: {int(row[23])} | State: {label_str}")

                if max_rows and rows_collected >= max_rows:
                    print(f"✓ Reached target {max_rows} rows.")
                    break

    except KeyboardInterrupt:
        print("\nCollector stopped by user.")

    print(f"Total live physical rows appended: {rows_collected}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live physical telemetry collector")
    parser.add_argument("--step", type=int, default=DEFAULT_STEP_INTERVAL, help="Seconds between window computations")
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum rows to collect before exiting")
    parser.add_argument("--label", type=int, choices=[0, 1], default=None, help="Force label: 0 (Normal) or 1 (Stress/Crash)")
    parser.add_argument("--tag", type=str, default=None, help="Scenario description tag (e.g., 'youtube_4k', 'memory_leak')")
    args = parser.parse_args()

    start_live_collection(
        step_interval=args.step,
        max_rows=args.max_rows,
        forced_label=args.label,
        tag=args.tag
    )
