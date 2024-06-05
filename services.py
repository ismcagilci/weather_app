import datetime
import os

import aiohttp
from dotenv import load_dotenv
from fastapi import HTTPException
from geopy.geocoders import Nominatim

from models import database, Weather

load_dotenv()


# Function to get the latitude and longitude of a city
async def get_lat_long(city_name):
    # Initialize the Nominatim geocoder
    geolocator = Nominatim(user_agent="weather-app")
    # Get the location data
    location = geolocator.geocode(city_name, language="en", timeout=20)
    if location:
        return location.latitude, location.longitude
    else:
        raise HTTPException(status_code=404, detail="City not found")


# Function to fetch weather data from the OpenWeatherMap API
async def fetch_weather_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Error fetching weather data")
            return await response.json()


# function to write data to the database
async def get_weather_data_and_write_to_db(city, date):
    API_KEY = os.getenv("API_KEY")
    lat_and_lon = await get_lat_long(city)
    lat, lon = lat_and_lon
    url = f"https://api.openweathermap.org/data/3.0/onecall/day_summary?lat={lat}&lon={lon}&date={date}&appid={API_KEY}&units=metric"
    weather_data = await fetch_weather_data(url)
    # insert the data into the database
    get_temps_by_celcius = weather_data["temperature"]
    # convert the temperature to Fahrenheit with 2 decimal places
    transform_to_fahrenheit = lambda c: round(c * 9 / 5 + 32, 2)
    get_temps_by_fahrenheit = {key: transform_to_fahrenheit(value) for key, value in get_temps_by_celcius.items()}
    insert_query = Weather.__table__.insert().values(city=city, date=date,
                                                     celcius=get_temps_by_celcius,
                                                     fahrenheit=get_temps_by_fahrenheit)
    await database.execute(insert_query)


# check the date format is correct "YYYY-MM-DD with a valid date"
# check the date about it is 7 days in the past or 7 days in the future
def validate_date(date):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD with a valid date")
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    today = datetime.datetime.now()
    if date > today + datetime.timedelta(days=7) or date < today - datetime.timedelta(days=7):
        raise HTTPException(status_code=400, detail="Date must be within 7 days from today")
