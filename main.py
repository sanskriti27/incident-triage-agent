# main.py
from kafka_consumer.consumer import start_consumer
from sample_service.seed_db import seed_db
import os

if __name__ == "__main__":
    # Seed DB if it doesn't exist yet
    if not os.path.exists("sample_service/transactions.db"):
        print("[Setup] Seeding database...")
        seed_db()

    # Start watching logs
    start_consumer()