import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
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

def create_postgres_database(db_name, user, password, host, port):

    con = psycopg2.connect(dbname=db_name, user=user, password=password, host=host, port=port)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created.")
    else:
        print(f"Database '{db_name}' already exists.")

    cur.close()
    con.close()

def init_db():
    create_postgres_database(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
