# openmeteo.py

import json
import datetime
import time
from pytz import timezone

WEATHER_TRANSLATIONS = {
    0: {
        "en": "Clear sky",
        "es": "Cielo despejado",
        "ca": "Cel clar",
        "gl": "Ceo despexado",
        "eu": "Zeru garbia",
    },
    1: {
        "en": "Mainly clear",
        "es": "Mayormente despejado",
        "ca": "Majoritàriament clar",
        "gl": "Maiormente despexado",
        "eu": "Nagusiki garbi",
    },
    2: {
        "en": "Partly cloudy",
        "es": "Parcialmente nublado",
        "ca": "Parcialment ennuvolat",
        "gl": "Parcialmente nubrado",
        "eu": "Hodei batzuk",
    },
    3: {
        "en": "Overcast",
        "es": "Nublado",
        "ca": "Ennuvolat",
        "gl": "Nubrado",
        "eu": "Estalita",
    },
    45: {
        "en": "Fog",
        "es": "Niebla",
        "ca": "Boira",
        "gl": "Néboa",
        "eu": "Lainoa",
    },
    48: {
        "en": "Depositing rime fog",
        "es": "Niebla con escarcha",
        "ca": "Boira gebradora",
        "gl": "Néboa con xeada",
        "eu": "Antzigar-lainoa",
    },
    51: {
        "en": "Drizzle: Light intensity",
        "es": "Llovizna ligera",
        "ca": "Plugim lleuger",
        "gl": "Poalla lixeira",
        "eu": "Zirimiri arina",
    },
    53: {
        "en": "Drizzle: Moderate intensity",
        "es": "Llovizna moderada",
        "ca": "Plugim moderat",
        "gl": "Poalla moderada",
        "eu": "Zirimiri moderatua",
    },
    55: {
        "en": "Drizzle: Dense intensity",
        "es": "Llovizna intensa",
        "ca": "Plugim intens",
        "gl": "Poalla intensa",
        "eu": "Zirimiri trinkoa",
    },
    56: {
        "en": "Freezing Drizzle: Light intensity",
        "es": "Llovizna engelante ligera",
        "ca": "Plugim gelant lleuger",
        "gl": "Poalla conxelante lixeira",
        "eu": "Zirimiri izozkor arina",
    },
    57: {
        "en": "Freezing Drizzle: Dense intensity",
        "es": "Llovizna engelante intensa",
        "ca": "Plugim gelant intens",
        "gl": "Poalla conxelante intensa",
        "eu": "Zirimiri izozkor trinkoa",
    },
    61: {
        "en": "Rain: Slight intensity",
        "es": "Lluvia ligera",
        "ca": "Pluja lleugera",
        "gl": "Chuvia lixeira",
        "eu": "Euri arina",
    },
    63: {
        "en": "Rain: Moderate intensity",
        "es": "Lluvia moderada",
        "ca": "Pluja moderada",
        "gl": "Chuvia moderada",
        "eu": "Euri moderatua",
    },
    65: {
        "en": "Rain: Heavy intensity",
        "es": "Lluvia intensa",
        "ca": "Pluja intensa",
        "gl": "Chuvia intensa",
        "eu": "Euri handia",
    },
    66: {
        "en": "Freezing Rain: Light intensity",
        "es": "Lluvia engelante ligera",
        "ca": "Pluja gelant lleugera",
        "gl": "Chuvia conxelante lixeira",
        "eu": "Euri izozkor arina",
    },
    67: {
        "en": "Freezing Rain: Heavy intensity",
        "es": "Lluvia engelante intensa",
        "ca": "Pluja gelant intensa",
        "gl": "Chuvia conxelante intensa",
        "eu": "Euri izozkor handia",
    },
    71: {
        "en": "Snow fall: Slight intensity",
        "es": "Nevada ligera",
        "ca": "Nevada lleugera",
        "gl": "Nevada lixeira",
        "eu": "Elur arina",
    },
    73: {
        "en": "Snow fall: Moderate intensity",
        "es": "Nevada moderada",
        "ca": "Nevada moderada",
        "gl": "Nevada moderada",
        "eu": "Elur moderatua",
    },
    75: {
        "en": "Snow fall: Heavy intensity",
        "es": "Nevada intensa",
        "ca": "Nevada intensa",
        "gl": "Nevada intensa",
        "eu": "Elur handia",
    },
    77: {
        "en": "Snow grains",
        "es": "Granos de nieve",
        "ca": "Grans de neu",
        "gl": "Grans de neve",
        "eu": "Elur-aleak",
    },
    80: {
        "en": "Rain showers: Slight intensity",
        "es": "Chubascos ligeros",
        "ca": "Ruixats lleugers",
        "gl": "Chuvascos lixeiros",
        "eu": "Zaparrada arinak",
    },
    81: {
        "en": "Rain showers: Moderate intensity",
        "es": "Chubascos moderados",
        "ca": "Ruixats moderats",
        "gl": "Chuvascos moderados",
        "eu": "Zaparrada moderatuak",
    },
    82: {
        "en": "Rain showers: Violent intensity",
        "es": "Chubascos fuertes",
        "ca": "Ruixats forts",
        "gl": "Chuvascos fortes",
        "eu": "Zaparrada handiak",
    },
    85: {
        "en": "Snow showers: Slight intensity",
        "es": "Chubascos de nieve ligeros",
        "ca": "Ruixats de neu lleugers",
        "gl": "Chuvascos de neve lixeiros",
        "eu": "Elur-zaparrada arinak",
    },
    86: {
        "en": "Snow showers: Heavy intensity",
        "es": "Chubascos de nieve intensos",
        "ca": "Ruixats de neu intensos",
        "gl": "Chuvascos de neve intensos",
        "eu": "Elur-zaparrada handiak",
    },
    95: {
        "en": "Thunderstorm: Slight or moderate",
        "es": "Tormenta eléctrica",
        "ca": "Tempesta elèctrica",
        "gl": "Treboada",
        "eu": "Ekaitza",
    },
    96: {
        "en": "Thunderstorm with slight hail",
        "es": "Tormenta eléctrica con granizo ligero",
        "ca": "Tempesta amb calamarsa lleugera",
        "gl": "Treboada con sarabia lixeira",
        "eu": "Ekaitza txingor arinarekin",
    },
    99: {
        "en": "Thunderstorm with heavy hail",
        "es": "Tormenta eléctrica con granizo intenso",
        "ca": "Tempesta amb calamarsa intensa",
        "gl": "Treboada con sarabia intensa",
        "eu": "Ekaitza txingor handiarekin",
    },
}

UNKNOWN_WEATHER = {
    "en": "Unknown",
    "es": "Desconocido",
    "ca": "Desconegut",
    "gl": "Descoñecido",
    "eu": "Ezezaguna",
}


def get_weather_translations(lang, wmocode):
    return WEATHER_TRANSLATIONS.get(wmocode, {}).get(
        lang, UNKNOWN_WEATHER.get(lang, UNKNOWN_WEATHER["en"]))

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
        56: 'chancesleet',
        57: 'sleet',
        61: 'chancerain',
        63: 'rain',
        65: 'rain',
        66: 'chancesleet',
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

    if filtered_num_hours > 0:
        darksky_data["hourly"]["summary"] = get_weather_translations(lang, filtered_hourly_data["weathercode"][0])
        darksky_data["hourly"]["icon"] = get_darksky_icon(filtered_hourly_data["weathercode"][0])
    else:
        darksky_data["hourly"]["summary"] = ""
        darksky_data["hourly"]["icon"] = "unknown"

    # Safe defaults from hourly data (used by daily and currently sections)
    hourly_dewpoint = filtered_hourly_data["dewpoint_2m"][0] if filtered_num_hours > 0 else 0
    hourly_humidity = filtered_hourly_data["relativehumidity_2m"][0] / 100 if filtered_num_hours > 0 else 0
    hourly_pressure = filtered_hourly_data["surface_pressure"][0] if filtered_num_hours > 0 else 0
    hourly_cloudcover = filtered_hourly_data["cloudcover_low"][0] if filtered_num_hours > 0 else 0
    hourly_visibility = filtered_hourly_data["visibility"][0] if filtered_num_hours > 0 else 0

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
        "dewPoint": hourly_dewpoint,
        "humidity": hourly_humidity,
        "pressure": hourly_pressure,
        "windSpeed": daily_data["windspeed_10m_max"][i],
        "windGust": daily_data["windgusts_10m_max"][i],
        "windGustTime": 0,
        "windBearing": daily_data["winddirection_10m_dominant"][i],
        "cloudCover": hourly_cloudcover,
        "uvIndex": daily_data["uv_index_max"][i],
        "uvIndexTime": 0,
        "visibility": hourly_visibility,
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
        "precipProbability": daily_data["precipitation_probability_mean"][0] / 100,
        "precipType": "rain",
        "temperature": json_data["current_weather"]["temperature"],
        "apparentTemperature": json_data["current_weather"]["temperature"],
        "dewPoint": hourly_dewpoint,
        "humidity": hourly_humidity,
        "pressure": hourly_pressure,
        "windSpeed": json_data["current_weather"]["windspeed"],
        "windGust": daily_data["windgusts_10m_max"][0],
        "windBearing": json_data["current_weather"]["winddirection"],
        "cloudCover": hourly_cloudcover,
        "uvIndex": daily_data["uv_index_max"][0],
        "visibility": hourly_visibility,
        "ozone": 0
        }

    return darksky_data
