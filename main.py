# main.py
import os
from dotenv import load_dotenv

load_dotenv()  # must be before ANY other import that uses env vars

from sample_service.seed_db import seed_db
from kafka_consumer.consumer import start_consumer

if __name__ == "__main__":
    # Seed DB if it doesn't exist yet
    if not os.path.exists("sample_service/transactions.db"):
        print("[Setup] Seeding database...")
        seed_db()

    # Start watching logs
    start_consumer()