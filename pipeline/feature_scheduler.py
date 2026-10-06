"""
Runs feature_builder.build_training_features() every COLLECTION_INTERVAL
seconds. The sleep subtracts the time the build took, so snapshots stay on a
steady 5-second cadence.
"""

import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import time

try:
    from pipeline.feature_builder import build_training_features
except ImportError:
    from feature_builder import build_training_features

HOST_ID = 1
COLLECTION_INTERVAL = 5


def main():

    print("==========================================")
    print("Feature Scheduler Started")
    print(f"Host ID : {HOST_ID}")
    print(f"Interval: {COLLECTION_INTERVAL} seconds")
    print("==========================================")

    while True:

        start_time = time.time()

        try:

            success = build_training_features(HOST_ID)

            if success:
                print("[Scheduler] Feature snapshot collected.")
            else:
                print("[Scheduler] Waiting for collector data...")

        except KeyboardInterrupt:

            print("\nFeature Scheduler stopped.")
            break

        except Exception as e:

            print(f"[Scheduler] Error: {e}")

        # Sleep only for the remainder of the interval so the period stays fixed
        elapsed = time.time() - start_time

        sleep_time = max(0, COLLECTION_INTERVAL - elapsed)

        time.sleep(sleep_time)


if __name__ == "__main__":

    main()