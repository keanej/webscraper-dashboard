# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    availability = Column(String, nullable=True)
    url = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_path="sqlite:///scraper_data.db"):
    return create_engine(db_path, echo=False, future=True)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
