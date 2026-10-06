"""
Feature snapshot builder.

Merges the latest row from each collector table (cpu, memory, disk, network,
runtime) into one row of model_training_features, using a single
INSERT ... SELECT so the merge happens inside PostgreSQL.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from core.db import get_connection
except ImportError:
    from db import get_connection


def build_training_features(host_id=1):
    """
    Insert one consolidated feature row for `host_id`.

    Network values are cumulative byte counters since boot, not per-second rates.

    Returns True on success, False if any collector table has no rows yet
    (the five single-row subqueries are cross-joined, so one empty table
    yields zero rows) or if the query fails.
    """

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO model_training_features
        (
            host_id,
            collected_at,
            cpu_usage,
            memory_usage,
            disk_usage,
            network_in,
            network_out,
            process_count,
            running_processes,
            thread_count,
            load_1,
            load_5,
            load_15
        )

        SELECT
            %s,
            NOW(),

            cpu.cpu_usage_percent,
            mem.memory_percent,
            disk.disk_percent,

            net.bytes_received,
            net.bytes_sent,

            runtime.total_processes,
            runtime.running_processes,
            runtime.thread_count,

            runtime.load_avg_1,
            runtime.load_avg_5,
            runtime.load_avg_15

        FROM

        (
            SELECT cpu_usage_percent
            FROM cpu_metrics
            WHERE host_id=%s
            ORDER BY collected_at DESC
            LIMIT 1
        ) cpu,

        (
            SELECT memory_percent
            FROM memory_metrics
            WHERE host_id=%s
            ORDER BY collected_at DESC
            LIMIT 1
        ) mem,

        (
            SELECT disk_percent
            FROM disk_metrics
            WHERE host_id=%s
            ORDER BY collected_at DESC
            LIMIT 1
        ) disk,

        (
            SELECT
                bytes_received,
                bytes_sent
            FROM network_metrics
            WHERE host_id=%s
            ORDER BY collected_at DESC
            LIMIT 1
        ) net,

        (
            SELECT
                total_processes,
                running_processes,
                thread_count,
                load_avg_1,
                load_avg_5,
                load_avg_15
            FROM system_runtime_info
            WHERE host_id=%s
            ORDER BY collected_at DESC
            LIMIT 1
        ) runtime
        """

        params = (
            host_id,
            host_id,
            host_id,
            host_id,
            host_id,
            host_id
        )

        cur.execute(query, params)

        if cur.rowcount == 0:

            conn.rollback()
            print("[Feature Builder] Waiting for collectors...")
            return False

        conn.commit()

        print("[Feature Builder] Feature snapshot collected.")

        return True

    except Exception as e:

        if conn:
            conn.rollback()

        print("[Feature Builder] Error:", e)

        return False

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":

    build_training_features()