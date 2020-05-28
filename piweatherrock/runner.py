# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import json
import pygame
import sys
import time

# pylint is mad about thise locals regardless of how they are used. with
# that being the case, I decided to have the lint error here instead of
# every place they get used. PR's welcome to make pylint happy about this
# and pygame.quit()
from pygame.locals import QUIT, VIDEORESIZE, KEYDOWN, K_KP_ENTER, K_q, K_d, K_h, K_i, K_s

# local imports
from piweatherrock.weather import Weather
from piweatherrock.plugin_weather_daily import PluginWeatherDaily
from piweatherrock.plugin_weather_hourly import PluginWeatherHourly
from piweatherrock.plugin_info import PluginInfo


class Runner:

    def __init__(self):
        self.current_screen = None
        self.d_count = 1
        self.h_count = 0
        self.running = False
        self.seconds = 0
        self.non_weather_timeout = 0
        self.periodic_info_activation = 0
        self.config = None
        self.my_weather_rock = None
        self.daily = None
        self.hourly = None
        self.info = None
        self.hourcap = 0
        self.caphour = False

    def main(self, config_file):
        with open(config_file, "r") as f:
            self.config = json.load(f)

        # Create an instance of the main application class
        self.my_weather_rock = Weather(config_file)

        # Create an instance of each plugin that will be used
        self.daily = PluginWeatherDaily(self.my_weather_rock)
        self.hourly = PluginWeatherHourly(self.my_weather_rock)
        self.info = PluginInfo(self.my_weather_rock)

        # Default to weather mode. Showing daily weather first.
        self.current_screen = 'd'

        self.d_count = 1
        self.h_count = 0

        # Stay running while True
        self.running = True

        # Seconds Placeholder to pace display
        self.seconds = 0

        # Display timeout to automatically switch back to weather display.
        self.non_weather_timeout = 0

        # Switch to info periodically to prevent screen burn.
        self.periodic_info_activation = 0

        # Loads data from darksky.net
        if not self.my_weather_rock.get_forecast():
            self.my_weather_rock.log.exception(
                "Error: no data from darksky.net.")
            self.running = False

        ##################################################################
        #                        Main progam loop                        #
        ##################################################################
        while self.running:
            # Look for and process keyboard events to change modes.
            self.process_pygame_events()
            self.screen_switcher()

            # Loop timer.
            pygame.time.wait(100)

        # When the main program loop is exited, exit the application
        pygame.quit()

    def process_pygame_events(self):
        """
        pygame events are how we learn about a window being closed or
        resized or a key being pressed. This function looks for the events
        we care about and reacts when needed.
        """

        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == VIDEORESIZE:
                self.my_weather_rock.sizing(event.size)
            elif event.type == KEYDOWN:

                # On 'q' or keypad enter key, quit the program.
                if ((event.key == K_KP_ENTER) or (event.key == K_q)):
                    self.running = False

                # On 'd' key, set mode to 'daily weather'.
                elif event.key == K_d:
                    self.current_screen = 'd'
                    self.d_count = 1
                    self.h_count = 0
                    self.non_weather_timeout = 0
                    self.periodic_info_activation = 0

                # on 'h' key, set mode to 'hourly weather'
                elif event.key == K_h:
                    self.current_screen = 'h'
                    self.d_count = 0
                    self.h_count = 1
                    self.non_weather_timeout = 0
                    self.periodic_info_activation = 0

                # On 'i' key, set mode to 'info'.
                elif event.key == K_i:
                    self.current_screen = 'i'
                    self.d_count = 0
                    self.h_count = 0
                    self.non_weather_timeout = 0
                    self.periodic_info_activation = 0

                # On 's' key, save a screen shot.
                elif event.key == K_s:
                    self.my_weather_rock.screen_cap()

    def screen_switcher(self):
        """
        This function takes care of cycling through the different screens
        on a regular basis.
        """

        # Automatically switch back to weather display after a couple minutes
        if self.current_screen not in ('d', 'h'):
            self.periodic_info_activation = 0
            self.non_weather_timeout += 1
            self.d_count = 0
            self.h_count = 0

            # Default in config.json.sample: pause for 5 minutes on info screen
            if self.non_weather_timeout > (self.config["info_pause"] * 10):
                self.current_screen = 'd'
                self.d_count = 1
                self.my_weather_rock.log.info("Switching to weather mode")
        else:
            self.non_weather_timeout = 0
            self.periodic_info_activation += 1

            # Default is to flip between 2 weather screens
            # for 15 minutes before showing info screen.
            if self.periodic_info_activation > (self.config["info_delay"] * 10):
                self.current_screen = 'i'
                self.my_weather_rock.log.info("Switching to info mode")
            elif (self.periodic_info_activation % (
                    ((self.config["plugins"]["daily"]["pause"] * self.d_count)
                        + (self.config["plugins"]["hourly"]["pause"] * self.h_count))
                    * 10)) == 0:
                if self.current_screen == 'd':
                    self.my_weather_rock.log.info("Switching to HOURLY")
                    self.current_screen = 'h'
                    self.h_count += 1
                else:
                    self.my_weather_rock.log.info("Switching to DAILY")
                    self.current_screen = 'd'
                    self.d_count += 1

        # Daily Weather Display Mode
        if self.current_screen == 'd':
            # Update / Refresh the display after each second.
            if self.seconds != time.localtime().tm_sec:
                self.seconds = time.localtime().tm_sec
                self.daily.disp_daily(self.my_weather_rock)
                # At first Daily screen of the new hour, capture it
                if self.config["caphour"]:
                    if time.localtime().tm_hour != self.hourcap:
                        self.my_weather_rock.screen_cap()
                        self.hourcap = time.localtime().tm_hour

            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, check to see if its time to get a
            # new set of data from the API.
            if self.seconds == 0:
                self.check_forecast()

        # Hourly Weather Display Mode
        elif self.current_screen == 'h':
            # Update / Refresh the display after each second.
            if self.seconds != time.localtime().tm_sec:
                self.seconds = time.localtime().tm_sec
                self.hourly.disp_hourly(self.my_weather_rock)

            # Once the screen is updated, we have a full second to get the
            # weather. Once per minute, check to see if its time to get a
            # new set of data from the API.
            if self.seconds == 0:
                self.check_forecast()

        # Info Screen Display Mode
        elif self.current_screen == 'i':
            # Pace the screen updates to once per second.
            if self.seconds != time.localtime().tm_sec:
                self.seconds = time.localtime().tm_sec

                # Disaplay information about the application along with the
                # time of sunrise and sunset.
                self.info.disp_info(self.my_weather_rock)

    def check_forecast(self):
        try:
            self.my_weather_rock.get_forecast()
        # includes simplejson.decoder.JSONDecodeError
        except ValueError:
            self.my_weather_rock.log.exception(
                f"Decoding JSON has failed: {sys.exc_info()[0]}")
        except BaseException:
            self.my_weather_rock.log.exception(
                f"Unexpected error: {sys.exc_info()[0]}")
