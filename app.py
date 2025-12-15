# app.py
from flask import Flask, render_template
from models import get_engine, Book
from sqlalchemy import select, func
from datetime import datetime

app = Flask(__name__)


def get_engine_obj():
    return get_engine()


@app.route("/")
def index():
    engine = get_engine_obj()
    with engine.connect() as conn:
        # latest 50 entries
        stmt = select(Book).order_by(Book.scraped_at.desc()).limit(50)
        rows = conn.execute(stmt).scalars().all()
        # simple aggregate: average price by day for last 14 days
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

    # prepare data for chart
    chart_data = {
        "labels": [row[0].isoformat() for row in reversed(agg)],
        "data": [round(row[1], 2) for row in reversed(agg)],
    }

    return render_template("index.html", books=rows, chart=chart_data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
