import json
import os
import time

import psutil

from db import get_connection

HOST_ID = 1
COLLECTION_INTERVAL = 2


def to_gb(value):
    return round(value / (1024 ** 3), 2)


def to_mb(value):
    return round(value / (1024 ** 2), 2)


def collect_disk_details():

    file_path = "disk_detailed_metrics.json"

    print(f"Disk Collector started... Writing to {os.path.abspath(file_path)}")

    while True:

        conn = None
        cur = None

        try:

            io_before = psutil.disk_io_counters()

            time.sleep(1)

            io_after = psutil.disk_io_counters()

            usage = psutil.disk_usage("/")

            read_rate = to_mb(
                io_after.read_bytes - io_before.read_bytes
            )

            write_rate = to_mb(
                io_after.write_bytes - io_before.write_bytes
            )

            partitions = []

            for part in psutil.disk_partitions():

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

                except PermissionError:
                    continue

            disk_metrics = {

                "total": f"{to_gb(usage.total)} GB",

                "used": f"{to_gb(usage.used)} GB",

                "free": f"{to_gb(usage.free)} GB",

                "percent": usage.percent,

                "read_rate": read_rate,

                "write_rate": write_rate,

                "partitions": partitions[:3]

            }

            with open(file_path, "w") as f:
                json.dump(disk_metrics, f, indent=4)

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
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
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

        time.sleep(COLLECTION_INTERVAL)


if __name__ == "__main__":

    collect_disk_details()