import time

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

        elapsed = time.time() - start_time

        sleep_time = max(0, COLLECTION_INTERVAL - elapsed)

        time.sleep(sleep_time)


if __name__ == "__main__":

    main()