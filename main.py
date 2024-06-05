import os

from fastapi import FastAPI
from pydantic import BaseModel

from models import database, Weather
from services import validate_date, get_weather_data_and_write_to_db

API_KEY = os.getenv("API_KEY")

app = FastAPI()


# Connect to the database when the app starts
@app.on_event("startup")
async def startup():
    await database.connect()


# Disconnect from the database when the app shuts down
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# define response model
class WeatherResponse(BaseModel):
    city: str
    date: str
    celcius: dict
    fahrenheit: dict


@app.get("/weather/{city}/{date}")
async def get_weather(city: str, date: str) -> WeatherResponse:
    validate_date(date)
    get_data_query = Weather.__table__.select().where(Weather.city == city, Weather.date == date)
    weather_data = await database.fetch_one(get_data_query)
    if not weather_data:
        await get_weather_data_and_write_to_db(city, date)
        weather_data = await database.fetch_one(get_data_query)
    return WeatherResponse(**dict(weather_data))
