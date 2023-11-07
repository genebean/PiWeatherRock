# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

# standard imports
import datetime
import os
import platform
import signal
import sys
import time
import json
import logging
import logging.handlers

# third party imports
from piweatherrock.climate import forecast
import pygame
import requests

# local imports
from piweatherrock.intl import intl


# globals
UNICODE_DEGREE = u'\xb0'

def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, exit_gracefully)


class Weather:
    """
    Fetches weather reports from Dark Sky for displaying on a screen.
    """

    def __init__(self, config_file):
        with open(config_file, "r") as f:
            self.config = json.load(f)

        #Initialize locale intl
        self.intl = intl()
        self.ui_lang = self.config["ui_lang"]

        # Initialize logger
        self.log = self.get_logger()

        self.last_update_check = 0
        self.weather = {}
        self.get_forecast()

        if platform.system() == 'Darwin':
            pygame.display.init()
            driver = pygame.display.get_driver()
            self.log.debug(f"Using the {driver} driver.")
        else:
            # Based on "Python GUI in Linux frame buffer"
            # http://www.karoltomala.com/blog/?p=679
            disp_no = os.getenv("DISPLAY")
            if disp_no:
                self.log.debug(f"X Display = {disp_no}")

            # Check which frame buffer drivers are available
            # Start with fbcon since directfb hangs with composite output
            drivers = ['x11', 'fbcon', 'directfb', 'svgalib']
            found = False
            for driver in drivers:
                # Make sure that SDL_VIDEODRIVER is set
                if not os.getenv('SDL_VIDEODRIVER'):
                    os.putenv('SDL_VIDEODRIVER', driver)
                try:
                    pygame.display.init()
                except pygame.error:
                    self.log.debug("Driver: {driver} failed.")
                    continue
                found = True
                break

            if not found:
                self.log.exception("No suitable video driver found!")

        size = (pygame.display.Info().current_w,
                pygame.display.Info().current_h)
        self.sizing(size)

        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()

        self.subwindow_text_height = 0.055
        self.time_date_text_height = 0.115
        self.time_date_small_text_height = 0.075
        self.time_date_y_position = 8
        self.time_date_small_y_position = 18

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def sizing(self, size):
        """
        Set various asplect of the app related to the screen size of
        the display and/or window.
        """

        self.log.debug(f"Framebuffer Size: {size[0]} x {size[1]}")

        if self.config["fullscreen"]:
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
            self.xmax = pygame.display.Info().current_w #  - 35 Why not use full screen in "fullescreen"?
            self.ymax = pygame.display.Info().current_h #  - 5 Why not use full screen in "fullescreen"?
        else:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            pygame.display.set_caption('PiWeatherRock')
            self.xmax = pygame.display.get_surface().get_width() - 35
            self.ymax = pygame.display.get_surface().get_height() - 5

        if self.xmax <= 1024:
            self.icon_size = '64'
        else:
            self.icon_size = '256'

    def get_logger(self):
        """
        Create a logger to be used for logging messages to a file. The
        verbosity of the logs is determined by the 'log_level' setting in
        the config file.
        """
        lvl_str = f"logging.{self.config['log_level']}"
        log = logging.getLogger()
        log.setLevel(eval(lvl_str))
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.handlers.RotatingFileHandler(
                ".log", maxBytes=500000, backupCount=3)
        if (log.hasHandlers()):
            log.handlers.clear()
        handler.setFormatter(formatter)
        log.addHandler(handler)

        return log

    def get_forecast(self):
        """
        Gets updated information if the 'update_freq' amount of time has
        passed since last querying the api.
        """
        if (time.time() - self.last_update_check) > self.config["update_freq"]:
            self.last_update_check = time.time()
            try:
                self.weather = forecast(
                    self.config["ds_api_key"],
                    self.config["lat"],
                    self.config["lon"],
                    exclude='minutely',
                    units=self.config["units"],
                    lang=self.config["lang"],
                    timezone=self.config["timezone"])
                
                sunset_today = datetime.datetime.fromtimestamp(
                    self.weather.daily[0].sunsetTime)
                if datetime.datetime.now() < sunset_today:
                    index = 0
                    sr_suffix = self.intl.get_text(self.ui_lang,"today")
                    ss_suffix = self.intl.get_text(self.ui_lang,"tonight")
                else:
                    index = 1
                    sr_suffix = self.intl.get_text(self.ui_lang,"tomorrow")
                    ss_suffix = self.intl.get_text(self.ui_lang,"tomorrow")

                self.sunrise = self.weather.daily[index].sunriseTime
                self.sunset = self.weather.daily[index].sunsetTime

                if self.config["12hour_disp"]:
                    self.sunrise_string = datetime.datetime.fromtimestamp(
                        self.sunrise).strftime("%I:%M %p {}").format(sr_suffix)
                    self.sunset_string = datetime.datetime.fromtimestamp(
                        self.sunset).strftime("%I:%M %p {}").format(ss_suffix)
                else:
                    self.sunrise_string = datetime.datetime.fromtimestamp(
                        self.sunrise).strftime("%H:%M {}").format(sr_suffix)
                    self.sunset_string = datetime.datetime.fromtimestamp(
                        self.sunset).strftime("%H:%M {}").format(ss_suffix)

            except requests.exceptions.RequestException as e:
                self.log.exception(f"Request exception: {e}")
                return False
            except AttributeError as e:
                self.log.exception(f"Attribute error: {e}")
                return False
        return True

    def screen_cap(self):
        """
        Save a jpg image of the screen
        """
        pygame.image.save(self.screen, "screenshot.jpeg")
        self.log.info("Screen capture complete.")
