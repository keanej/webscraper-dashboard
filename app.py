# app.py
from flask import Flask, render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select
from scraper.scraper import scrape_catalog

from models import get_engine, Book

app = Flask(__name__)

# create session factory
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)


@app.route("/")
def index():
    engine = get_engine_obj()

    # AUTO-POPULATE DB ON FIRST RUN (Render-safe)
    with engine.connect() as conn:
        count = conn.execute(select(func.count()).select_from(Book)).scalar()

    if count == 0:
        # scrape first page only to keep startup fast
        scrape_catalog(page_limit=1, delay=1.5)

    with engine.connect() as conn:
        stmt = select(Book).order_by(Book.scraped_at.desc()).limit(50)
        rows = conn.execute(stmt).scalars().all()

        agg_stmt = (
            select(
                func.date(Book.scraped_at).label("day"),
                func.avg(Book.price).label("avg_price"),
            )
            .group_by(func.date(Book.scraped_at))
            .order_by(func.date(Book.scraped_at).desc())
            .limit(14)
        )
        agg = conn.execute(agg_stmt).all()

    chart_data = {
        "labels": [row[0] for row in reversed(agg)],
        "data": [round(row[1], 2) for row in reversed(agg)],
    }

    return render_template("index.html", books=rows, chart=chart_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
