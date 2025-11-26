from sqlalchemy import create_engine, Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Define the SQLite database URL
DATABASE_URL = "sqlite:///movies.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a base class for declarative models
Base = declarative_base()


# Define the Movie model (adjust columns as per movies.csv)
class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_name = Column(String, nullable=False)
    year = Column(Integer)
    genres = Column(JSON)
    rating = Column(Float)


# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)


def create_all_tables():
    Base.metadata.create_all(engine)


# Dependency to get DB session
@contextmanager
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass
