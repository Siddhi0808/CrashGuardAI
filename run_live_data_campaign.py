"""
run_live_data_campaign.py

Interactive Live Physical Data Collection Campaign for CrashGuard AI.
Guides you through collecting authentic hardware telemetry across diverse
system states (Normal vs Crash Precursors) with zero target leakage.
"""

import os
import sys
import time
import subprocess
import threading

VENV_PYTHON = sys.executable if sys.executable else os.path.abspath("./aibsv/bin/python")
COLLECTOR_SCRIPT = "collect_live_physical_data.py"

def run_collector(duration_sec, label, tag):
    """
    Runs collect_live_physical_data.py for the specified duration with explicit label and tag.
    """
    cmd = [
        VENV_PYTHON,
        COLLECTOR_SCRIPT,
        "--step", "2",
        "--label", str(label),
        "--tag", tag
    ]
    print(f"\n[Starting Collector] Duration: {duration_sec}s | Label: {label} ({'CRASH/STRESS' if label == 1 else 'NORMAL'}) | Tag: '{tag}'")
    proc = subprocess.Popen(cmd)
    
    try:
        time.sleep(duration_sec)
    except KeyboardInterrupt:
        print("\nSession interrupted early by user.")
    finally:
        proc.terminate()
        proc.wait()
        print(f"[Finished] Scenario '{tag}' complete.\n")


# Controlled real physical workload functions
def stress_cpu(duration_sec):
    stop_event = threading.Event()
    def worker():
        while not stop_event.is_set():
            _ = 99999999 * 99999999
    
    threads = [threading.Thread(target=worker) for _ in range(os.cpu_count() or 4)]
    for t in threads:
        t.start()
    time.sleep(duration_sec)
    stop_event.set()
    for t in threads:
        t.join()


def stress_memory(duration_sec, target_mb=4000):
    """
    Safely allocates real memory chunks in RAM to generate genuine physical memory pressure.
    """
    print(f"Allocating ~{target_mb}MB in real RAM...")
    data = []
    chunk = b'x' * (10 * 1024 * 1024) # 10MB
    for _ in range(target_mb // 10):
        data.append(chunk)
        time.sleep(0.05)
    print("Memory allocated. Holding pressure...")
    time.sleep(max(1, duration_sec - 10))
    del data


def stress_threads(duration_sec, num_threads=150):
    """
    Spawns real physical worker threads to generate genuine thread scheduler queue load.
    """
    stop_event = threading.Event()
    def worker():
        while not stop_event.is_set():
            time.sleep(0.01)
    
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    time.sleep(duration_sec)
    stop_event.set()
    for t in threads:
        t.join()


def main_menu():
    print("=" * 65)
    print("   CrashGuard AI - Live Hardware Data Collection Campaign")
    print("=" * 65)
    print("Select a physical scenario to record into dataset.csv:\n")
    print("  [1] Normal: Idle / Background (leave system quiet for 60s)")
    print("  [2] Normal: Everyday Multitasking (browse, YouTube, coding for 90s)")
    print("  [3] Normal: Heavy Benign Compute (multi-core load without crashing, 60s)")
    print("  [4] Crash Precursor: Real CPU Starvation Loop (pegs CPU cores, 60s)")
    print("  [5] Crash Precursor: Real Physical Memory Pressure (allocates RAM, 60s)")
    print("  [6] Crash Precursor: Real Thread Scheduler Storm (spawns 150 threads, 60s)")
    print("  [7] Custom Session (enter your own duration and label)")
    print("  [8] Run Automated Full Suite (cycles through scenarios 1-6)")
    print("  [0] Exit")
    print("=" * 65)

    choice = input("\nEnter choice [0-8]: ").strip()

    if choice == "1":
        print("\nKeep system quiet for 60s...")
        run_collector(60, label=0, tag="physical_idle")
    elif choice == "2":
        print("\nBrowse the web, play a video, or write code for 90s...")
        run_collector(90, label=0, tag="physical_multitask")
    elif choice == "3":
        print("\nRunning heavy benign compute for 60s...")
        w_thread = threading.Thread(target=stress_cpu, args=(55,))
        w_thread.start()
        run_collector(60, label=0, tag="benign_compute")
        w_thread.join()
    elif choice == "4":
        print("\nTriggering real CPU starvation loop for 60s...")
        w_thread = threading.Thread(target=stress_cpu, args=(55,))
        w_thread.start()
        run_collector(60, label=1, tag="cpu_runaway_loop")
        w_thread.join()
    elif choice == "5":
        print("\nTriggering real memory allocation leak for 60s...")
        w_thread = threading.Thread(target=stress_memory, args=(55, 3500))
        w_thread.start()
        run_collector(60, label=1, tag="memory_pressure_leak")
        w_thread.join()
    elif choice == "6":
        print("\nTriggering thread scheduler queue explosion for 60s...")
        w_thread = threading.Thread(target=stress_threads, args=(55, 150))
        w_thread.start()
        run_collector(60, label=1, tag="thread_queue_storm")
        w_thread.join()
    elif choice == "7":
        dur = int(input("Enter duration in seconds (e.g. 60): ").strip() or "60")
        lbl = int(input("Enter label (0 for Normal, 1 for Crash/Stress): ").strip() or "0")
        tag = input("Enter tag description: ").strip() or "custom"
        run_collector(dur, label=lbl, tag=tag)
    elif choice == "8":
        print("\nStarting Automated Live Suite (6 minutes total)...")
        print("\n--- Phase 1: Idle (60s) ---")
        run_collector(60, label=0, tag="auto_idle")
        print("\n--- Phase 2: Normal Load (60s) ---")
        run_collector(60, label=0, tag="auto_normal")
        print("\n--- Phase 3: Heavy Benign Compute (60s) ---")
        t_cpu = threading.Thread(target=stress_cpu, args=(55,))
        t_cpu.start()
        run_collector(60, label=0, tag="auto_benign_compute")
        t_cpu.join()
        print("\n--- Phase 4: Real CPU Starvation (60s) ---")
        t_starve = threading.Thread(target=stress_cpu, args=(55,))
        t_starve.start()
        run_collector(60, label=1, tag="auto_cpu_starvation")
        t_starve.join()
        print("\n--- Phase 5: Real Memory Ramp (60s) ---")
        t_mem = threading.Thread(target=stress_memory, args=(55, 3500))
        t_mem.start()
        run_collector(60, label=1, tag="auto_memory_leak")
        t_mem.join()
        print("\n--- Phase 6: Real Thread Storm (60s) ---")
        t_threads = threading.Thread(target=stress_threads, args=(55, 150))
        t_threads.start()
        run_collector(60, label=1, tag="auto_thread_storm")
        t_threads.join()
        print("\n✓ Automated Live Physical Campaign complete!")
    else:
        print("Exiting.")

if __name__ == "__main__":
    main_menu()
