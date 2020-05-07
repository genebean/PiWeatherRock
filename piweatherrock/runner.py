# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import json
import pygame
import sys
import time

# local imports
from piweatherrock import utils
from piweatherrock.weather import Weather
from piweatherrock.plugin_weather_daily import PluginWeatherDaily
from piweatherrock.plugin_weather_hourly import PluginWeatherHourly


def main(config_file):
    with open(config_file, "r") as f:
        CONFIG = json.load(f)

    # Create an instance of the lcd display class.
    MY_DISP = Weather(config_file)
    SIZES = {
        'xmax': MY_DISP.xmax,
        'ymax': MY_DISP.ymax,
        'time_date_small_text_height': MY_DISP.time_date_small_text_height,
        'time_date_text_height': MY_DISP.time_date_text_height,
        'time_date_y_position': MY_DISP.time_date_y_position,
        'time_date_small_y_position': MY_DISP.time_date_small_y_position,
        'subwindow_text_height': MY_DISP.subwindow_text_height,
        'icon_size': MY_DISP.icon_size,
    }

    HOURLY = PluginWeatherHourly(
        MY_DISP.screen, MY_DISP.weather, MY_DISP.config, SIZES)

    DAILY = PluginWeatherDaily(
        MY_DISP.screen, MY_DISP.weather, MY_DISP.config, SIZES)

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
    if not MY_DISP.get_forecast():
        MY_DISP.log.exception("Error: no data from darksky.net.")
        RUNNING = False

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    while RUNNING:
        # Look for and process keyboard events to change modes.
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
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
                    MY_DISP.screen_cap()

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
                MY_DISP.log.info("Switching to weather mode")
        else:
            NON_WEATHER_TIMEOUT = 0
            PERIODIC_INFO_ACTIVATION += 1
            # Default is to flip between 2 weather screens
            # for 15 minutes before showing info screen.
            if PERIODIC_INFO_ACTIVATION > (CONFIG["info_delay"] * 10):
                MODE = 'i'
                MY_DISP.log.info("Switching to info mode")
            elif (PERIODIC_INFO_ACTIVATION % (
                    ((CONFIG["plugins"]["daily"]["pause"] * D_COUNT)
                     + (CONFIG["plugins"]["hourly"]["pause"] * H_COUNT))
                    * 10)) == 0:
                if MODE == 'd':
                    MY_DISP.log.info("Switching to HOURLY")
                    MODE = 'h'
                    H_COUNT += 1
                else:
                    MY_DISP.log.info("Switching to DAILY")
                    MODE = 'd'
                    D_COUNT += 1

        # Daily Weather Display Mode
        if MODE == 'd':
            # Update / Refresh the display after each second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec
                DAILY.disp_daily()

            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, update the weather from the net.
            if SECONDS == 0:
                try:
                    MY_DISP.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_DISP.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_DISP.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")
        # Hourly Weather Display Mode
        elif MODE == 'h':
            # Update / Refresh the display after each second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec
                HOURLY.disp_hourly()
            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, update the weather from the net.
            if SECONDS == 0:
                try:
                    MY_DISP.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_DISP.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_DISP.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")
        # Info Screen Display Mode
        elif MODE == 'i':
            # Pace the screen updates to once per second.
            if SECONDS != time.localtime().tm_sec:
                SECONDS = time.localtime().tm_sec

                (inDaylight, dayHrs, dayMins, seconds_til_daylight,
                 delta_seconds_til_dark) = utils.daylight(MY_DISP.weather)

                # Extra info display.
                MY_DISP.disp_info(inDaylight, dayHrs, dayMins,
                                  seconds_til_daylight,
                                  delta_seconds_til_dark)
            # Refresh the weather data once per minute.
            if int(SECONDS) == 0:
                try:
                    MY_DISP.get_forecast()
                # includes simplejson.decoder.JSONDecodeError
                except ValueError:
                    MY_DISP.log.exception(
                        f"Decoding JSON has failed: {sys.exc_info()[0]}")
                except BaseException:
                    MY_DISP.log.exception(
                        f"Unexpected error: {sys.exc_info()[0]}")

        (inDaylight, dayHrs, dayMins, seconds_til_daylight,
         delta_seconds_til_dark) = utils.daylight(MY_DISP.weather)

        # Loop timer.
        pygame.time.wait(100)

    pygame.quit()
