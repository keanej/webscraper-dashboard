# app.py
from flask import Flask, render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select

from models import get_engine, Book

app = Flask(__name__)

# create session factory
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)


@app.route("/")
def index():
    session = SessionLocal()
    try:
        # latest 50 books (ORM objects)
        books = session.query(Book).order_by(Book.scraped_at.desc()).limit(50).all()

        # average price per day (aggregates)
        agg = (
            session.query(
                func.date(Book.scraped_at),
                func.avg(Book.price),
            )
            .group_by(func.date(Book.scraped_at))
            .order_by(func.date(Book.scraped_at).desc())
            .limit(14)
            .all()
        )
    finally:
        session.close()

    # prepare data for chart
    chart_data = {
        "labels": [row[0] for row in reversed(agg)],
        "data": [round(row[1], 2) for row in reversed(agg)],
    }

    return render_template(
        "index.html",
        books=books,
        chart=chart_data,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
