from sqlalchemy import create_engine, Column, Integer, String, Text  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore
from dotenv import load_dotenv
from models import Base, UserToken
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
BROKER = os.getenv("BROKER")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
CELERY_BACKEND_URL = "db+" + DATABASE_URL
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
