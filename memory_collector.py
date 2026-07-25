import json
import os
import time

import psutil

from db import get_connection

HOST_ID = 1
COLLECTION_INTERVAL = 2


def collect_memory_details():

    file_path = "memory_detailed_metrics.json"

    print(f"Memory Collector started... Writing to {os.path.abspath(file_path)}")

    while True:

        conn = None
        cur = None

        try:

            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            def to_gb(value):
                return round(value / (1024 ** 3), 2)

            memory_metrics = {

                "total": f"{to_gb(mem.total)} GB",
                "used": f"{to_gb(mem.used)} GB",
                "free": f"{to_gb(mem.free)} GB",
                "available": f"{to_gb(mem.available)} GB",

                "cached": f"{to_gb(getattr(mem, 'cached', 0))} GB",
                "buffers": f"{to_gb(getattr(mem, 'buffers', 0))} GB",

                "swap_total": f"{to_gb(swap.total)} GB",
                "swap_used": f"{to_gb(swap.used)} GB",
                "swap_percent": swap.percent,

                "percent": mem.percent,

                "composition": {
                    "used": mem.used,
                    "cached": getattr(mem, "cached", 0),
                    "buffers": getattr(mem, "buffers", 0),
                    "free": mem.free
                }

            }

            with open(file_path, "w") as f:
                json.dump(memory_metrics, f, indent=4)

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO memory_metrics
                (
                    host_id,
                    memory_percent,
                    swap_percent
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    HOST_ID,
                    float(mem.percent),
                    float(swap.percent)
                )
            )

            conn.commit()

        except Exception as e:

            if conn:
                conn.rollback()

            print(f"Memory Collector Error: {e}")

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

        time.sleep(COLLECTION_INTERVAL)


if __name__ == "__main__":

    collect_memory_details()