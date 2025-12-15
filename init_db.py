# init_db.py
from models import init_db, get_engine

if __name__ == "__main__":
    init_db(get_engine())
    print("DB initialized.")
