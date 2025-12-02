from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base
import os

DATABASE_DIR = Path(__file__).parents[1]

DATABASE_PATH = DATABASE_DIR / 'university_data.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={'check_same_thread': False}
)

SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_PATH}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")

