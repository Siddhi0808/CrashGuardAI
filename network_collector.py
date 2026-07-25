import json
import os
import time

import psutil

from db import get_connection

HOST_ID = 1
COLLECTION_INTERVAL = 2


def to_mb(value):
    return round(value / (1024 ** 2), 2)


def collect_network_details():

    file_path = "network_detailed_metrics.json"

    print(f"Network Collector started... Writing to {os.path.abspath(file_path)}")

    while True:

        conn = None
        cur = None

        try:

            net_before = psutil.net_io_counters()

            time.sleep(1)

            net_after = psutil.net_io_counters()

            incoming_rate = to_mb(
                net_after.bytes_recv - net_before.bytes_recv
            )

            outgoing_rate = to_mb(
                net_after.bytes_sent - net_before.bytes_sent
            )

            interfaces = []

            pernic = psutil.net_io_counters(pernic=True)
            stats = psutil.net_if_stats()

            for name in pernic:

                interfaces.append({

                    "interface": name,

                    "sent": f"{to_mb(pernic[name].bytes_sent)} MB",

                    "recv": f"{to_mb(pernic[name].bytes_recv)} MB",

                    "status": "UP" if stats[name].isup else "DOWN"

                })

            network_metrics = {

                "bytes_sent": f"{to_mb(net_after.bytes_sent)} MB",

                "bytes_recv": f"{to_mb(net_after.bytes_recv)} MB",

                "incoming_rate": incoming_rate,

                "outgoing_rate": outgoing_rate,

                "pkts_sent": net_after.packets_sent,

                "pkts_recv": net_after.packets_recv,

                "errin": net_after.errin,

                "errout": net_after.errout,

                "interfaces": interfaces[:3]

            }

            with open(file_path, "w") as f:
                json.dump(network_metrics, f, indent=4)

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO network_metrics
                (
                    host_id,
                    bytes_sent,
                    bytes_received,
                    incoming_rate,
                    outgoing_rate
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    HOST_ID,
                    int(net_after.bytes_sent),
                    int(net_after.bytes_recv),
                    float(incoming_rate),
                    float(outgoing_rate)
                )
            )

            conn.commit()

        except Exception as e:

            if conn:
                conn.rollback()

            print(f"Network Collector Error: {e}")

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

        time.sleep(COLLECTION_INTERVAL)


if __name__ == "__main__":

    collect_network_details()