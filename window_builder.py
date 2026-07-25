import time

import numpy as np
import pandas as pd
from scipy.stats import linregress

from db import get_connection

WINDOW_SIZE = 60
WINDOW_STEP = 30


def calculate_trend(series):

    series = pd.Series(series).ffill().bfill()

    if len(series) < 2:
        return 0.0

    x = np.arange(len(series))

    slope, _, _, _, _ = linregress(x, series)

    return float(slope)


def safe_std(series):

    value = float(series.std())

    if np.isnan(value):
        return 0.0

    return value


def safe_variance(series):

    value = float(series.var())

    if np.isnan(value):
        return 0.0

    return value


def build_window():

    conn = None
    cur = None

    try:

        conn = get_connection()

        query = f"""
        SELECT
            collected_at,
            cpu_usage,
            memory_usage,
            disk_usage,
            network_in,
            network_out,
            process_count,
            running_processes,
            thread_count
        FROM model_training_features
        ORDER BY collected_at DESC
        LIMIT {WINDOW_SIZE}
        """

        df = pd.read_sql(query, conn)

        if len(df) < WINDOW_SIZE:
            print(f"Waiting for {WINDOW_SIZE} samples... ({len(df)}/{WINDOW_SIZE})")
            return

        df = df.sort_values("collected_at").reset_index(drop=True)

        start_time = df.iloc[0]["collected_at"]
        end_time = df.iloc[-1]["collected_at"]

        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1
            FROM system_feature_windows
            WHERE end_time=%s
            LIMIT 1
            """,
            (end_time,)
        )

        if cur.fetchone():

            print("Window already exists.")
            return

        cpu = df["cpu_usage"]
        memory = df["memory_usage"]
        disk = df["disk_usage"]

        net_in = df["network_in"]
        net_out = df["network_out"]

        process = df["process_count"]
        running = df["running_processes"]
        threads = df["thread_count"]

        values = (

            start_time,
            end_time,

            float(cpu.mean()),
            float(cpu.max()),
            float(cpu.min()),
            float(safe_std(cpu)),
            float(calculate_trend(cpu)),
            float(cpu.max() - cpu.min()),
            float(safe_variance(cpu)),

            float(memory.mean()),
            float(memory.max()),
            float(memory.min()),
            float(safe_std(memory)),
            float(memory.max() - memory.min()),
            float(calculate_trend(memory)),

            float(disk.mean()),
            float(disk.max()),
            float(disk.min()),
            float(safe_std(disk)),
            float(disk.max() - disk.min()),
            float(calculate_trend(disk)),

            float(net_in.mean()),
            float(net_out.mean()),
            float(safe_std(net_in)),
            float(safe_std(net_out)),

            float(process.mean()),
            float(process.max()),
            float(process.min()),
            float(safe_std(process)),

            float(running.mean()),
            float(threads.mean()),

            0.0
        )

        cur.execute(
            """
            INSERT INTO system_feature_windows
            (
                start_time,
                end_time,

                cpu_avg,
                cpu_max,
                cpu_min,
                cpu_std,
                cpu_trend,
                cpu_range,
                cpu_variance,

                memory_avg,
                memory_max,
                memory_min,
                memory_std,
                memory_range,
                memory_trend,

                disk_avg,
                disk_max,
                disk_min,
                disk_std,
                disk_range,
                disk_trend,

                network_in_avg,
                network_out_avg,
                network_in_std,
                network_out_std,

                process_avg,
                process_max,
                process_min,
                process_std,

                running_process_avg,
                thread_avg,

                swap_avg
            )
            VALUES
            (
                %s,%s,

                %s,%s,%s,%s,%s,%s,%s,

                %s,%s,%s,%s,%s,%s,

                %s,%s,%s,%s,%s,%s,

                %s,%s,%s,%s,

                %s,%s,%s,%s,

                %s,%s,

                %s
            )
            """,
            values
        )

        conn.commit()

        print("✓ Window stored successfully")

    except Exception as e:

        if conn:
            conn.rollback()

        print("Window Builder Error:", e)

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":

    while True:

        build_window()

        time.sleep(WINDOW_STEP)