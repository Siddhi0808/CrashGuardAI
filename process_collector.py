import json
import os
import time

import psutil

from db import get_connection

HOST_ID = 1
COLLECTION_INTERVAL = 3


def collect_and_save():

    file_path = "process_metrics.json"

    print(f"Process Collector started... Writing to {os.path.abspath(file_path)}")

    while True:

        conn = None
        cur = None

        try:

            counts = {
                "total": 0,
                "running": 0,
                "sleeping": 0,
                "stopped": 0,
                "zombie": 0,
                "threads": 0
            }

            processes = []

            attrs = [
                "pid",
                "ppid",
                "name",
                "username",
                "num_threads",
                "status",
                "cpu_percent",
                "memory_percent"
            ]

            for proc in psutil.process_iter(attrs):

                try:

                    info = proc.info

                    counts["total"] += 1
                    counts["threads"] += info["num_threads"] or 0

                    status = info["status"]

                    if status == psutil.STATUS_RUNNING:
                        counts["running"] += 1

                    elif status == psutil.STATUS_SLEEPING:
                        counts["sleeping"] += 1

                    elif status == psutil.STATUS_STOPPED:
                        counts["stopped"] += 1

                    elif status == psutil.STATUS_ZOMBIE:
                        counts["zombie"] += 1

                    try:

                        io = proc.io_counters()

                        read_value = f"{io.read_bytes / (1024**2):.2f} MB"
                        write_value = f"{io.write_bytes / (1024**2):.2f} MB"

                    except (psutil.AccessDenied, AttributeError):

                        read_value = "0.00 MB"
                        write_value = "0.00 MB"

                    processes.append({

                        "pid": info["pid"],

                        "ppid": info["ppid"],

                        "process": info["name"] or "Unknown",

                        "user": info["username"] or "System",

                        "cpu": f"{info['cpu_percent'] or 0:.1f}%",

                        "memory": f"{info['memory_percent'] or 0:.2f}%",

                        "threads": info["num_threads"] or 0,

                        "status": str(status).upper(),

                        "read": read_value,

                        "write": write_value

                    })

                except (psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess):

                    continue

            processes.sort(
                key=lambda x: float(x["cpu"].replace("%", "")),
                reverse=True
            )

            with open(file_path, "w") as f:

                json.dump(
                    {
                        "summary": counts,
                        "processes": processes[:50]
                    },
                    f,
                    indent=4
                )

            load1, load5, load15 = os.getloadavg()

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO system_runtime_info
                (
                    host_id,
                    total_processes,
                    running_processes,
                    sleeping_processes,
                    stopped_processes,
                    zombie_processes,
                    thread_count,
                    load_avg_1,
                    load_avg_5,
                    load_avg_15
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    HOST_ID,
                    counts["total"],
                    counts["running"],
                    counts["sleeping"],
                    counts["stopped"],
                    counts["zombie"],
                    counts["threads"],
                    float(load1),
                    float(load5),
                    float(load15)
                )
            )

            conn.commit()

        except Exception as e:

            if conn:
                conn.rollback()

            print(f"Process Collector Error: {e}")

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

        time.sleep(COLLECTION_INTERVAL)


if __name__ == "__main__":

    collect_and_save()