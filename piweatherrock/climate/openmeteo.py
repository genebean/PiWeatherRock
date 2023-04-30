# openmeteo.py

import json
import datetime
import time
from pytz import timezone

def get_weather_translations(lang, wmocode):
    weather_translations = {
      0: {"en": "Clear sky", "es": "Cielo despejado"},
      1: {"en": "Mainly clear", "es": "Mayormente despejado"},
      2: {"en": "Partly cloudy", "es": "Parcialmente nublado"},
      3: {"en": "Overcast", "es": "Nublado"},
      45: {"en": "Fog", "es": "Niebla"},
      48: {"en": "Depositing rime fog", "es": "Niebla depositada"},
      51: {"en": "Drizzle: Light intensity", "es": "Llovizna: Intensidad ligera"},
      53: {"en": "Drizzle: Moderate intensity", "es": "Llovizna: Intensidad moderada"},
      55: {"en": "Drizzle: Dense intensity", "es": "Llovizna: Intensidad densa"},
      56: {"en": "Freezing Drizzle: Light intensity", "es": "Llovizna helada: Intensidad ligera"},
      57: {"en": "Freezing Drizzle: Dense intensity", "es": "Llovizna helada: Intensidad densa"},
      61: {"en": "Rain: Slight intensity", "es": "Lluvia: Intensidad ligera"},
      63: {"en": "Rain: Moderate intensity", "es": "Lluvia: Intensidad moderada"},
      65: {"en": "Rain: Heavy intensity", "es": "Lluvia: Intensidad fuerte"},
      66: {"en": "Freezing Rain: Light intensity", "es": "Lluvia helada: Intensidad ligera"},
      67: {"en": "Freezing Rain: Heavy intensity", "es": "Lluvia helada: Intensidad fuerte"},
      71: {"en": "Snow fall: Slight intensity", "es": "Nevada: Intensidad ligera"},
      73: {"en": "Snow fall: Moderate intensity", "es": "Nevada: Intensidad moderada"},
      75: {"en": "Snow fall: Heavy intensity", "es": "Nevada: Intensidad fuerte"},
      77: {"en": "Snow grains", "es": "Granos de nieve"},
      80: {"en": "Rain showers: Slight intensity", "es": "Lluvias: Intensidad ligera"},
      81: {"en": "Rain showers: Moderate intensity", "es": "Lluvias: Intensidad moderada"},
      82: {"en": "Rain showers: Violent intensity", "es": "Lluvias: Intensidad fuerte"},
      85: {"en": "Snow showers: Slight intensity", "es": "Nevadas: Intensidad ligera"},
      86: {"en": "Snow showers: Heavy intensity", "es": "Nevadas: Intensidad fuerte"},
      95: {"en": "Thunderstorm: Slight or moderate", "es": "Tormenta eléctrica: Ligera o moderada"},
      96: {"en": "Thunderstorm with slight hail", "es": "Tormenta eléctrica con granizo ligero"},
      99: {"en": "Thunderstorm with heavy hail", "es": "Tormenta eléctrica con granizo fuerte"}
    }
    return weather_translations.get(wmocode, {}).get(lang, "Unknown" if lang == "en" else "Desconocido")

def get_darksky_icon(wmocode):
    icon_map = {
        0: 'clear',
        1: 'mostlysunny',
        2: 'partlycloudy',
        3: 'cloudy',
        45: 'fog',
        48: 'hazy',
        51: 'chancerain',
        53: 'rain',
        55: 'rain',
        56: 'chainsleet',
        57: 'sleet',
        61: 'chancerain',
        63: 'rain',
        65: 'rain',
        66: 'chainsleet',
        67: 'sleet',
        71: 'chancesnow',
        73: 'chancesnow',
        75: 'snow',
        77: 'snow',
        80: 'rain',
        81: 'rain',
        82: 'rain',
        85: 'chanceflurries',
        86: 'flurries',
        95: 'tstorm',
        96: 'chancetstorms',
        99: 'tstorms'
    }
    return icon_map.get(wmocode, 'unknown')

def openmeteo_to_darksky(data, lang):
    darksky_data = {}
    json_data = json.loads(data)

    # Latitude, Longitude and Timezone
    darksky_data["latitude"] = json_data["latitude"]
    darksky_data["longitude"] = json_data["longitude"]
    darksky_data["timezone"] = json_data["timezone"]

    # Current weather data
    current_date_obj = datetime.datetime.fromisoformat(json_data["current_weather"]["time"])
    current_unix_timestamp = int(time.mktime(current_date_obj.timetuple()))

    # Get the first day for the current weather, and set the variable dor daily and hourly
    daily_data = json_data["daily"]
    hourly_data = json_data["hourly"]

    # Hourly weather data
    darksky_data["hourly"] = {
        "summary": "",
        "icon": "",
        "data": []
    }

    # Filter time array to get only the 4 next records based on current time 
    time_zone_str = json_data["timezone"]
    tz = timezone(time_zone_str)
    current_datetime = datetime.datetime.now(tz)
    upper_limit = current_datetime + datetime.timedelta(hours=4)

    filtered_hourly_data = {}
    indexes = []

    for key in hourly_data.keys():
      if key == 'time':
        filtered_hourly_data[key] = []
        for i, date_value in enumerate(hourly_data[key]):
          date_obj = tz.localize(datetime.datetime.fromisoformat(date_value))
          if current_datetime <= date_obj < upper_limit:
            filtered_hourly_data[key].append(hourly_data[key][i])
            indexes.append(i)

    for key in hourly_data.keys():
      if key != 'time':
        filtered_hourly_data[key] = []
        for i in indexes:
          filtered_hourly_data[key].append(hourly_data[key][i])

    filtered_num_hours = len(filtered_hourly_data["time"])
    for i in range(filtered_num_hours):
      time_date_obj = datetime.datetime.fromisoformat(filtered_hourly_data["time"][i])
      time_unix_timestamp = int(time.mktime(time_date_obj.timetuple()))

      darksky_hour_data = {
        "time": time_unix_timestamp,
        "summary": get_weather_translations(lang, filtered_hourly_data["weathercode"][i]),
        "icon": get_darksky_icon(filtered_hourly_data["weathercode"][i]),
        "precipIntensity": filtered_hourly_data["precipitation_probability"][i],
        "precipProbability": filtered_hourly_data["precipitation_probability"][i] / 100,
        "precipType": "rain",
        "temperature": filtered_hourly_data["temperature_2m"][i],
        "apparentTemperature": filtered_hourly_data["apparent_temperature"][i],
        "dewPoint": filtered_hourly_data["dewpoint_2m"][i],
        "humidity": filtered_hourly_data["relativehumidity_2m"][i] / 100,
        "pressure": filtered_hourly_data["surface_pressure"][i],
        "windSpeed": filtered_hourly_data["windspeed_10m"][i],
        "windGust": filtered_hourly_data["windgusts_10m"][i],
        "windBearing": filtered_hourly_data["winddirection_10m"][i],
        "cloudCover": filtered_hourly_data["cloudcover_low"][i],
        "uvIndex": filtered_hourly_data["direct_radiation"][i],
        "visibility": filtered_hourly_data["visibility"][i],
        "ozone": 0,
      }
      darksky_data["hourly"]["data"].append(darksky_hour_data)
    darksky_data["hourly"]["summary"] = get_weather_translations(lang, filtered_hourly_data["weathercode"][0])
    darksky_data["hourly"]["icon"] = get_darksky_icon(filtered_hourly_data["weathercode"][0])

    # Daily weather data
    darksky_data["daily"] = {
        "summary": get_weather_translations(lang, daily_data["weathercode"][0]),
        "icon": get_darksky_icon(daily_data["weathercode"][0]),
        "data": []
    }

    num_days = len(daily_data['time'])

    for i in range(num_days):
      time_date_obj = datetime.datetime.fromisoformat(daily_data["time"][i])
      time_unix_timestamp = int(time.mktime(time_date_obj.timetuple()))

      sunset_date_obj = datetime.datetime.fromisoformat(daily_data["sunset"][i])
      sunset_unix_timestamp = int(time.mktime(sunset_date_obj.timetuple()))

      sunrise_date_obj = datetime.datetime.fromisoformat(daily_data["sunrise"][i])
      sunrise_unix_timestamp = int(time.mktime(sunrise_date_obj.timetuple()))

      darksky_day_data = {
        "time": time_unix_timestamp,
        "summary": get_weather_translations(lang, daily_data["weathercode"][i]),
        "icon": get_darksky_icon(daily_data["weathercode"][i]),
        "sunriseTime": sunrise_unix_timestamp,
        "sunsetTime": sunset_unix_timestamp,
        "temperatureHigh": daily_data["temperature_2m_max"][i],
        "temperatureLow": daily_data["temperature_2m_min"][i],
        "moonPhase": 0,
        "precipIntensity": daily_data["precipitation_probability_min"][i],
        "precipIntensityMax": daily_data["precipitation_probability_max"][i],
        "precipIntensityMaxTime": 0,
        "precipProbability": daily_data["precipitation_probability_mean"][i] / 100,
        "precipType": "rain",
        "temperatureHighTime": 0,
        "temperatureLowTime": 0,
        "apparentTemperatureHigh": daily_data["apparent_temperature_max"][i],
        "apparentTemperatureHighTime": 0,
        "apparentTemperatureLow": daily_data["apparent_temperature_min"][i],
        "apparentTemperatureLowTime": 0,
        "dewPoint": filtered_hourly_data["dewpoint_2m"][0],
        "humidity": filtered_hourly_data["relativehumidity_2m"][0] / 100,
        "pressure": filtered_hourly_data["surface_pressure"][0],
        "windSpeed": daily_data["windspeed_10m_max"][i],
        "windGust": daily_data["windgusts_10m_max"][i],
        "windGustTime": 0,
        "windBearing": daily_data["winddirection_10m_dominant"][i],
        "cloudCover": filtered_hourly_data["cloudcover_low"][0],
        "uvIndex": daily_data["uv_index_max"][i],
        "uvIndexTime": 0,
        "visibility": filtered_hourly_data["visibility"][0],
        "ozone": 0,
        "temperatureMin": daily_data["temperature_2m_min"][i],
        "temperatureMinTime": 0,
        "temperatureMax": daily_data["temperature_2m_max"][i],
        "temperatureMaxTime": 0,
        "apparentTemperatureMin": daily_data["apparent_temperature_min"][i],
        "apparentTemperatureMinTime": 0,
        "apparentTemperatureMax": daily_data["apparent_temperature_max"][i],
        "apparentTemperatureMaxTime": 0,
      }
      darksky_data["daily"]["data"].append(darksky_day_data)

    darksky_data["currently"] = {
        "time": current_unix_timestamp,
        "summary": get_weather_translations(lang, daily_data["weathercode"][0]),
        "icon": get_darksky_icon(daily_data["weathercode"][0]),
        "nearestStormDistance": 0,
        "precipIntensity": daily_data["precipitation_probability_min"][0],
        "precipIntensityError": 0,
        "precipProbability": daily_data["precipitation_probability_mean"][0] /,
        "precipType": "rain",
        "temperature": json_data["current_weather"]["temperature"],
        "apparentTemperature": json_data["current_weather"]["temperature"],
        "dewPoint": filtered_hourly_data["dewpoint_2m"][0],
        "humidity": filtered_hourly_data["relativehumidity_2m"][0] / 100,
        "pressure": filtered_hourly_data["surface_pressure"][0],
        "windSpeed": json_data["current_weather"]["windspeed"],
        "windGust": daily_data["windgusts_10m_max"][0],
        "windBearing": json_data["current_weather"]["winddirection"],
        "cloudCover": filtered_hourly_data["cloudcover_low"][0],
        "uvIndex": daily_data["uv_index_max"][0],
        "visibility": filtered_hourly_data["visibility"][0],
        "ozone": 0
        }

    return darksky_data