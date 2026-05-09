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
import logging
import logging.handlers

# third party imports
from piweatherrock.climate import forecast
import pygame
import requests

# local imports
from piweatherrock.config_manager import (
    DISPLAY_RELOAD_PATHS,
    LOG_RELOAD_PATHS,
    SUN_TIME_RELOAD_PATHS,
    WEATHER_RELOAD_PATHS,
    config_changed,
    load_config,
)
from piweatherrock.intl import intl


# globals
UNICODE_DEGREE = u'\xb0'

def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, exit_gracefully)


class Weather:
    """
    Fetches weather reports from Open-Meteo API for displaying on a screen.
    """

    def __init__(self, config_file):
        self.config = load_config(config_file)

        #Initialize locale intl
        self.intl = intl()
        self.ui_lang = self.config["ui_lang"]

        # Initialize logger
        self.log = self.get_logger()

        self.last_update_check = 0
        self.weather = {}
        self.get_forecast()

        self._init_display()

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

    def _init_display(self):
        system = platform.system()
        if system != 'Linux':
            pygame.display.init()
            driver = pygame.display.get_driver()
            self.log.debug("Using the %s driver on %s.", driver, system)
            return

        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            self.log.debug(f"X Display = {disp_no}")

        configured_driver = os.getenv('SDL_VIDEODRIVER')
        if configured_driver:
            try:
                pygame.display.init()
            except pygame.error:
                self.log.critical(
                    "Configured SDL video driver %s failed.",
                    configured_driver)
                sys.exit(1)
            self.log.debug("Using the %s driver.", pygame.display.get_driver())
            return

        # Check which frame buffer drivers are available.
        # Start with x11, then fall back to framebuffer drivers for Raspberry Pi.
        drivers = ['x11', 'fbcon', 'directfb', 'svgalib']
        for driver in drivers:
            os.environ['SDL_VIDEODRIVER'] = driver
            try:
                pygame.display.init()
            except pygame.error:
                pygame.display.quit()
                self.log.debug("Driver %s failed.", driver)
                continue
            self.log.debug("Using the %s driver.", pygame.display.get_driver())
            return

        os.environ.pop('SDL_VIDEODRIVER', None)
        self.log.critical("No suitable video driver found!")
        sys.exit(1)

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
        log_level = getattr(logging, self.config['log_level'].upper(), logging.INFO)
        log = logging.getLogger()
        log.setLevel(log_level)
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
            try:
                self.weather = forecast(
                    self.config["ds_api_key"],
                    self.config["lat"],
                    self.config["lon"],
                    exclude='minutely',
                    units=self.config["units"],
                    lang=self.config["lang"],
                    timezone=self.config["timezone"])
                
                self.update_sun_strings()

                # Only update the check time after a successful fetch
                self.last_update_check = time.time()

            except requests.exceptions.RequestException as e:
                self.log.exception(f"Request exception: {e}")
                return False
            except AttributeError as e:
                self.log.exception(f"Attribute error: {e}")
                return False
        return True

    def reload_config(self, new_config, changed_paths):
        """
        Apply a validated configuration change without restarting the UI.
        """
        self.config = new_config
        self.ui_lang = self.config["ui_lang"]

        if config_changed(changed_paths, LOG_RELOAD_PATHS):
            self.log = self.get_logger()

        if config_changed(changed_paths, DISPLAY_RELOAD_PATHS):
            size = (pygame.display.Info().current_w,
                    pygame.display.Info().current_h)
            self.sizing(size)
            self.screen.fill((0, 0, 0))
            pygame.display.update()

        if config_changed(changed_paths, WEATHER_RELOAD_PATHS):
            self.last_update_check = 0
            self.get_forecast()
        elif config_changed(changed_paths, SUN_TIME_RELOAD_PATHS):
            self.update_sun_strings()

    def update_sun_strings(self):
        """
        Compute sunrise and sunset strings from current weather and display settings.
        """
        daily = getattr(self.weather, "daily", None)
        if daily is None:
            return

        sunset_today = datetime.datetime.fromtimestamp(
            daily[0].sunsetTime)

        if datetime.datetime.now() < sunset_today:
            index = 0
            sr_suffix = self.intl.get_text(self.ui_lang, "today")
            ss_suffix = self.intl.get_text(self.ui_lang, "tonight")
        else:
            index = 1
            sr_suffix = self.intl.get_text(self.ui_lang, "tomorrow")
            ss_suffix = self.intl.get_text(self.ui_lang, "tomorrow")

        self.sunrise = daily[index].sunriseTime
        self.sunset = daily[index].sunsetTime

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

    def screen_cap(self):
        """
        Save a jpg image of the screen
        """
        pygame.image.save(self.screen, "screenshot.jpeg")
        self.log.info("Screen capture complete.")
