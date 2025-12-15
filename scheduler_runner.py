# scheduler_runner.py
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.scraper import scrape_catalog
from models import get_engine, init_db
import os


def job():
    print("Scheduler job starting: scraping...")
    try:
        scrape_catalog(
            page_limit=1,
            delay=1.5,
            db_path=os.getenv("DATABASE_URL", "sqlite:///scraper_data.db"),
        )
    except Exception as ex:
        print("Error in scheduled job:", ex)
    print("Scheduler job finished.")


def start_scheduler():
    sched = BackgroundScheduler()
    # run every hour (example). Adjust to your needs.
    sched.add_job(job, "interval", minutes=60, next_run_time=None)
    sched.start()
    return sched


if __name__ == "__main__":
    # ensure DB exists
    engine = get_engine()
    init_db(engine)
    start_scheduler()
    # import and run flask app
    from app import app

    app.run(debug=False, host="0.0.0.0", port=5000)
