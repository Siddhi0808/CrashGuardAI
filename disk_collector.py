import json
import os
import time
import psutil
from db import get_connection

HOST_ID = 1
COLLECTION_INTERVAL = 2
TARGET_MOUNT = "/" if os.name != "nt" else "C:\\"


def to_gb(value):
    return round(value / (1024 ** 3), 2)


def to_mb(value):
    return round(value / (1024 ** 2), 2)


def collect_disk_details():
    file_path = "disk_detailed_metrics.json"
    print(f"Disk Collector started... Writing to {os.path.abspath(file_path)}")

    # Initialize baseline counter and timestamp
    prev_io = psutil.disk_io_counters()
    prev_time = time.time()

    while True:
        conn = None
        cur = None

        try:

            time.sleep(COLLECTION_INTERVAL)

            curr_io = psutil.disk_io_counters()
            curr_time = time.time()

            time_delta = curr_time - prev_time
            if time_delta <= 0:
                time_delta = 1.0

            # Calculate I/O throughput (MB/s) over actual elapsed time
            read_bytes_delta = curr_io.read_bytes - prev_io.read_bytes
            write_bytes_delta = curr_io.write_bytes - prev_io.write_bytes

            read_rate = to_mb(read_bytes_delta / time_delta)
            write_rate = to_mb(write_bytes_delta / time_delta)

            # Update baselines for next iteration
            prev_io = curr_io
            prev_time = curr_time

            # Disk Usage
            usage = psutil.disk_usage(TARGET_MOUNT)

            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    p_usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mount": part.mountpoint,
                        "filesystem": part.fstype,
                        "used": f"{to_gb(p_usage.used)} GB",
                        "free": f"{to_gb(p_usage.free)} GB",
                        "percent": p_usage.percent
                    })
                except (PermissionError, OSError):
                    continue

            disk_metrics = {
                "total": f"{to_gb(usage.total)} GB",
                "used": f"{to_gb(usage.used)} GB",
                "free": f"{to_gb(usage.free)} GB",
                "percent": usage.percent,
                "read_rate_mbps": read_rate,
                "write_rate_mbps": write_rate,
                "partitions": partitions[:3]
            }

            # Dump JSON state
            with open(file_path, "w") as f:
                json.dump(disk_metrics, f, indent=4)

            # Database Insertion
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO disk_metrics
                (
                    host_id,
                    disk_percent,
                    read_rate,
                    write_rate
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    HOST_ID,
                    float(usage.percent),
                    float(read_rate),
                    float(write_rate)
                )
            )

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Disk Collector Error: {e}")

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


if __name__ == "__main__":
    collect_disk_details()