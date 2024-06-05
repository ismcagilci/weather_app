import os

from databases import Database
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, MetaData, JSON
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create an async engine and a database instance
database = Database(DATABASE_URL)
metadata = MetaData()

Base = declarative_base()


class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    date = Column(String, index=True)
    celcius = Column(JSON)
    fahrenheit = Column(JSON)


# Create the database tables
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
