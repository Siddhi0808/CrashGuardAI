import pandas as pd
from datetime import timedelta

from db import get_connection


PREDICTION_WINDOW_MINUTES = 5


def label_windows():

    conn = None
    cur = None

    try:

        conn = get_connection()

        windows = pd.read_sql(
            """
            SELECT
                id,
                end_time,
                crash_label
            FROM system_feature_windows
            ORDER BY end_time
            """,
            conn
        )

        if windows.empty:
            print("No feature windows found.")
            return

        events = pd.read_sql(
            """
            SELECT
                event_time
            FROM system_events
            WHERE event_type IN ('CRASH', 'MANUAL_TEST_CRASH')
            ORDER BY event_time
            """,
            conn
        )

        windows["new_label"] = 0

        if not events.empty:

            for crash_time in events["event_time"]:

                start_time = crash_time - timedelta(
                    minutes=PREDICTION_WINDOW_MINUTES
                )

                mask = (
                    (windows["end_time"] >= start_time) &
                    (windows["end_time"] < crash_time)
                )

                windows.loc[mask, "new_label"] = 1

        cur = conn.cursor()

        updates = 0

        for _, row in windows.iterrows():

            current = (
                0 if pd.isna(row["crash_label"])
                else int(row["crash_label"])
            )

            new = int(row["new_label"])

            if current == new:
                continue

            cur.execute(
                """
                UPDATE system_feature_windows
                SET crash_label=%s
                WHERE id=%s
                """,
                (
                    new,
                    int(row["id"])
                )
            )

            updates += 1

        conn.commit()

        positives = int(windows["new_label"].sum())

        print("===================================")
        print("Window Labeling Complete")
        print("===================================")
        print(f"Positive windows : {positives}")
        print(f"Negative windows : {len(windows)-positives}")
        print(f"Rows updated     : {updates}")

    except Exception as e:

        if conn:
            conn.rollback()

        print("Labeling Error:", e)

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":

    label_windows()