"""
CPU collector: every ~2 s (1 s sampling + 1 s sleep), records total/user/system/idle
CPU %, per-core load and context switches to data/runtime/cpu_detailed_metrics.json
and inserts total CPU % into the cpu_metrics table.

Note: "temperature" and the frequency fallback are fixed placeholder values,
not sensor readings (psutil cannot read these on Apple Silicon).
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import json
import os
import time

import psutil

try:
    from core.db import get_connection
    from core.config import RUNTIME_DATA_DIR
except ImportError:
    from db import get_connection
    RUNTIME_DATA_DIR = "."


def get_cpu_frequency():
    """
    Returns CPU frequency.
    Uses a fallback value for Apple Silicon.
    """
    try:
        freq = psutil.cpu_freq()

        if freq and freq.current:
            return f"{freq.current / 1000:.2f} GHz"

    except Exception:
        pass

    return "3.20 GHz"


def collect_cpu_details():

    file_path = os.path.join(RUNTIME_DATA_DIR, "cpu_detailed_metrics.json")

    print(f"CPU Collector started... Writing to {os.path.abspath(file_path)}")

    while True:

        conn = None
        cur = None

        try:

            # Blocks for 1 s to measure the CPU time split over that interval
            cpu_times = psutil.cpu_times_percent(interval=1)

            # Non-blocking: overall CPU % since the previous cpu_percent() call
            cpu_usage = psutil.cpu_percent(interval=None)

            cpu_metrics = {

                "total_usage": cpu_usage,

                "user": cpu_times.user,
                "system": cpu_times.system,
                "idle": cpu_times.idle,
                "iowait": getattr(cpu_times, "iowait", 0.0),

                "frequency": get_cpu_frequency(),

                "cores": psutil.cpu_percent(
                    interval=None,
                    percpu=True
                ),

                "ctx_switches": psutil.cpu_stats().ctx_switches,

                "interrupts": psutil.cpu_stats().interrupts,

                "temperature": "48°C"

            }

            with open(file_path, "w") as f:
                json.dump(cpu_metrics, f, indent=4)

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO cpu_metrics
                (
                    host_id,
                    cpu_usage_percent
                )
                VALUES
                (
                    %s,
                    %s
                )
                """,
                (
                    1,
                    cpu_usage
                )
            )

            conn.commit()

        except Exception as e:

            if conn:
                conn.rollback()

            print("CPU Collector Error:", e)

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

        time.sleep(1)


if __name__ == "__main__":

    collect_cpu_details()