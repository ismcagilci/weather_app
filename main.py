import os
from typing import Literal, List, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import select, and_

from models import database, Weather
from services import validate_date, get_weather_data_and_write_to_db, create_date_list

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
    celcius: Optional[Dict] = None
    fahrenheit: Optional[Dict] = None


class DateType(BaseModel):
    start_date: str
    end_date: str
    type: Literal['f', 'c']


@app.post("/weather/{city}")
async def get_weather(city: str, data_type: DateType) -> List[WeatherResponse]:
    validate_date(data_type.start_date, data_type.end_date)

    # Determine the column to select based on the data type
    column = Weather.celcius if data_type.type == "c" else Weather.fahrenheit

    # Query to get data within the date range
    get_datas_query = select(Weather.city, Weather.date, column).where(
        and_(
            Weather.city == city,
            Weather.date <= data_type.end_date,
            Weather.date >= data_type.start_date
        )
    )
    weather_datas = await database.fetch_all(get_datas_query)
    get_date_list = create_date_list(data_type.start_date, data_type.end_date)
    if len(weather_datas) != len(get_date_list):
        for date in get_date_list:
            get_data_query = select(Weather).where(
                and_(
                    Weather.city == city,
                    Weather.date == date
                )
            )
            weather_data = await database.fetch_one(get_data_query)
            if not weather_data:
                await get_weather_data_and_write_to_db(city, date)
        weather_datas = await database.fetch_all(get_datas_query)
    return [dict(data) for data in weather_datas]
