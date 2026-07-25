from db import get_connection


def build_training_features(host_id=1):

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