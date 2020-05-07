# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import json
import pygame
import sys
import time

# local imports
from piweatherrock.weather import Weather
from piweatherrock.plugin_weather_daily import PluginWeatherDaily
from piweatherrock.plugin_weather_hourly import PluginWeatherHourly
from piweatherrock.plugin_info import PluginInfo


def main(config_file):
    with open(config_file, "r") as f:
        CONFIG = json.load(f)

    # Create an instance of the lcd display class.
    MY_WEATHER_ROCK = Weather(config_file)

    DAILY = PluginWeatherDaily(MY_WEATHER_ROCK)
    HOURLY = PluginWeatherHourly(MY_WEATHER_ROCK)
    INFO = PluginInfo(MY_WEATHER_ROCK)

    MODE = 'd'  # Default to weather mode. Showing daily weather first.

    D_COUNT = 1
    H_COUNT = 0

    RUNNING = True             # Stay running while True
    SECONDS = 0                # Seconds Placeholder to pace display.
    # Display timeout to automatically switch back to weather display.
    NON_WEATHER_TIMEOUT = 0
    # Switch to info periodically to prevent screen burn.
    PERIODIC_INFO_ACTIVATION = 0

    # Loads data from darksky.net into class variables.
    if not MY_WEATHER_ROCK.get_forecast():
        MY_WEATHER_ROCK.log.exception("Error: no data from darksky.net.")
        RUNNING = False

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    while RUNNING:
        # Look for and process keyboard events to change modes.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                RUNNING = False
            elif event.type == pygame.VIDEORESIZE:
                MY_WEATHER_ROCK.sizing(event.size)
            elif event.type == pygame.KEYDOWN:
                # On 'q' or keypad enter key, quit the program.
                if ((event.key == pygame.K_KP_ENTER) or (event.key == pygame.K_q)):
                    RUNNING = False

                # On 'd' key, set mode to 'weather'.
                elif event.key == pygame.K_d:
                    MODE = 'd'
                    D_COUNT = 1
                    H_COUNT = 0
                    NON_WEATHER_TIMEOUT = 0
                    PERIODIC_INFO_ACTIVATION = 0

                # On 's' key, save a screen shot.
                elif event.key == pygame.K_s:
                    MY_WEATHER_ROCK.screen_cap()

                # On 'i' key, set mode to 'info'.
                elif event.key == pygame.K_i:
                    MODE = 'i'
                    D_COUNT = 0
                    H_COUNT = 0
                    NON_WEATHER_TIMEOUT = 0
                    PERIODIC_INFO_ACTIVATION = 0

                # on 'h' key, set mode to 'hourly'
                elif event.key == pygame.K_h:
                    MODE = 'h'
                    D_COUNT = 0
                    H_COUNT = 1
                    NON_WEATHER_TIMEOUT = 0
                    PERIODIC_INFO_ACTIVATION = 0

        # Automatically switch back to weather display after a couple minutes.
        if MODE not in ('d', 'h'):
            PERIODIC_INFO_ACTIVATION = 0
            NON_WEATHER_TIMEOUT += 1
            D_COUNT = 0
            H_COUNT = 0
            # Default in config.py.sample: pause for 5 minutes on info screen.
            if NON_WEATHER_TIMEOUT > (CONFIG["info_pause"] * 10):
                MODE = 'd'
                D_COUNT = 1
                MY_WEATHER_ROCK.log.info("Switching to weather mode")
        else:
            NON_WEATHER_TIMEOUT = 0
            PERIODIC_INFO_ACTIVATION += 1
            # Default is to flip between 2 weather screens
            # for 15 minutes before showing info screen.
            if PERIODIC_INFO_ACTIVATION > (CONFIG["info_delay"] * 10):
                MODE = 'i'
                MY_WEATHER_ROCK.log.info("Switching to info mode")
            elif (PERIODIC_INFO_ACTIVATION % (
                    ((CONFIG["plugins"]["daily"]["pause"] * D_COUNT)
                     + (CONFIG["plugins"]["hourly"]["pause"] * H_COUNT))
                    * 10)) == 0:
                if MODE == 'd':
                    MY_WEATHER_ROCK.log.info("Switching to HOURLY")
                    MODE = 'h'
                    H_COUNT += 1
                else:
                    MY_WEATHER_ROCK.log.info("Switching to DAILY")
                    MODE = 'd'
                    D_COUNT += 1

        # Daily Weather Display Mode
        if MODE == 'd':
            # Update / Refresh the display after each second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec
                DAILY.disp_daily(MY_WEATHER_ROCK)

            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, update the weather from the net.
            if SECONDS == 0:
                try:
                    MY_WEATHER_ROCK.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_WEATHER_ROCK.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_WEATHER_ROCK.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")
        # Hourly Weather Display Mode
        elif MODE == 'h':
            # Update / Refresh the display after each second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec
                HOURLY.disp_hourly(MY_WEATHER_ROCK)
            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, update the weather from the net.
            if SECONDS == 0:
                try:
                    MY_WEATHER_ROCK.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_WEATHER_ROCK.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_WEATHER_ROCK.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")
        # Info Screen Display Mode
        elif MODE == 'i':
            # Pace the screen updates to once per second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec

                # Extra info display.
                INFO.disp_info(MY_WEATHER_ROCK)
            # Refresh the weather data once per minute.
            if int(SECONDS) == 0:
                try:
                    MY_WEATHER_ROCK.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_WEATHER_ROCK.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_WEATHER_ROCK.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")

        # Loop timer.
        pygame.time.wait(100)

    pygame.quit()
