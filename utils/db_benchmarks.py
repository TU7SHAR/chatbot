import time
from app import app
from models.models import db, Bot, Organization

def run_benchmarks():
    with app.app_context():
        print("--- Starting Neon DB Benchmarks ---")
        
        start = time.time()
        bot_count = Bot.query.count()
        end = time.time()
        print(f"Latency (Simple Count): {(end - start) * 1000:.2f} ms")

        start = time.time()
        bots = Bot.query.filter_by(org_id=2).all() 
        end = time.time()
        print(f"Latency (Filtered Fetch): {(end - start) * 1000:.2f} ms")

        print("-----------------------------------")

if __name__ == "__main__":
    run_benchmarks()