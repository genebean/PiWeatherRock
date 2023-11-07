# forecast.py
from __future__ import print_function
from builtins import super

import json
import sys
import requests
from os import path

import logging
from http.client import HTTPConnection

# Enable HTTPConnection debug logging to stdout.
log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
log.addHandler(stream_handler)

from .data import DataPoint
from .openmeteo import *

# format from:
# https://open-meteo.com/en/docs#latitude=40.31&longitude=-3.73&hourly=temperature_2m
# info for mapping: https://openweathermap.org/darksky-openweather-3
_API_URL = "https://api.open-meteo.com/v1/forecast"
_LOAD_FROM_FILE_ = False  # Set this to True to load JSON from a file, or False to make an HTTP GET request

class Forecast(DataPoint):
    def __init__(self, key, latitude, longitude, time=None, timeout=None, **queries):
        self._parameters = dict(key=key, latitude=latitude, longitude=longitude, time=time)
        self.refresh(timeout, **queries)

    def __setattr__(self, key, value):
        if key in ('_queries', '_parameters', '_data'):
            return object.__setattr__(self, key, value)
        return super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in self.currently._data.keys():
            return self.currently._data[key]
        return object.__getattribute__(self, key)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        del self

    def load_json_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    
    @property
    def url(self):
        time = self._parameters['time']
        timestr = ',{}'.format(time) if time else ''
        config = {
            "forecast_days": 4,
            "models": "best_match",
            "current_weather": "true",
            "temperature_unit": "celsius",
            "windspeed_unit": "kmh",
            "precipitation_unit": "mm",
            "timeformat": "iso8601",
            "hourly":"visibility,weathercode,temperature_2m,relativehumidity_2m,apparent_temperature,surface_pressure,cloudcover,windspeed_80m,precipitation,precipitation_probability,dewpoint_2m,windspeed_10m,windgusts_10m,winddirection_10m,cloudcover_low,direct_radiation",
            "daily":"sunrise,sunset,uv_index_max,weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_mean,precipitation_probability_min,windgusts_10m_max,precipitation_probability_max,windspeed_10m_max,winddirection_10m_dominant"
        }

        uri_format = '{url}?latitude={latitude}&longitude={longitude}&appid={key}&timezone={timezone}&models={models}&forecast_days={forecast_days}&current_weather={current_weather}&temperature_unit={temperature_unit}&windspeed_unit={windspeed_unit}&precipitation_unit={precipitation_unit}&timeformat={timeformat}&hourly={hourly}&daily={daily}'
        return uri_format.format(
            url=_API_URL, 
            timestr=timestr,
            timezone = self._queries["timezone"],
            forecast_days = config["forecast_days"],
            current_weather = config["current_weather"],
            models = config["models"],
            temperature_unit = config["temperature_unit"],
            windspeed_unit = config["windspeed_unit"],
            precipitation_unit = config["precipitation_unit"],
            timeformat = config["timeformat"],
            hourly = config["hourly"],
            daily = config["daily"],
            **self._parameters)

    def refresh(self, timeout=None, **queries):
        self._queries = queries
        self.timeout = timeout
        request_params = {
            'params': self._queries,
            'headers': {'Accept-Encoding': 'gzip'},
            'timeout': timeout
        }

        if _LOAD_FROM_FILE_:
            file_path = path.join(path.dirname(__file__),'data','example.json')
            data = self.load_json_file(file_path)

            return super().__init__(data)
        else:
            response = requests.get(self.url)
            self.response_headers = response.headers
            if response.status_code != 200:
                print(response.text)
                raise requests.exceptions.HTTPError('Bad response')

            return super().__init__(openmeteo_to_darksky(response.text, queries["lang"]))
