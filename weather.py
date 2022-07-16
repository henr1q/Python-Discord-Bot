import json
import requests
import os
import asyncio

API_TOKEN = os.environ.get('WEATHER_TOKEN')


def get_coord(city):

    city_name = city
    state_code = ''
    country_code = 'BR'  # set your country code
    limit = 1


    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_code},{country_code}&limit={limit}&appid={API_TOKEN}'


    data = requests.get(url,)
    if data.status_code == 200:
        data = data.json()
        name = data[0]['name']
        lat = data[0]['lat']
        lon = data[0]['lon']
        state = data[0]['state']
        return {'name': name, 'lat': lat, 'lon': lon, 'state': state}
    else:
        return f'API returned: code {data.status_code}'


def get_clima(lat, lon):

    parameters = {
        'lat': lat,
        'lon': lon,
        # 'lang': 'pt_br',  # set your lang
        'appid': API_TOKEN,
        'units': 'Metric'
    }

    url = 'https://api.openweathermap.org/data/2.5/weather'

    data = requests.get(url, params=parameters).json()
    temp = data['main']['temp']
    humidity = data['main']['humidity']
    desc = data['weather'][0]['description']


    return {'temp': temp, 'desc': desc, 'humidity': humidity}

