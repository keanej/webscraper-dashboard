from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(Float)
    availability = Column(String)
    url = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_url="sqlite:///scraper_data.db"):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)  # 👈 THIS LINE IS THE FIX
    return engine
