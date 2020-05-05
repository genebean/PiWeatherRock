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
from darksky import forecast
import pygame
import requests

from piweatherrock import utils


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

        self.last_update_check = 0
        self.weather = {}
        self.get_forecast()
        # Initialize logger
        self.log = self.get_logger()

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
        self.log.debug(f"Framebuffer Size: {size[0]} x {size[1]}")
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()

        if self.config["fullscreen"]:
            self.xmax = pygame.display.Info().current_w - 35
            self.ymax = pygame.display.Info().current_h - 5
            if self.xmax <= 1024:
                self.icon_size = '64'
            else:
                self.icon_size = '256'
        else:
            self.xmax = 480 - 35
            self.ymax = 320 - 5
            self.icon_size = '64'

        self.subwindow_text_height = 0.055
        self.time_date_text_height = 0.115
        self.time_date_small_text_height = 0.075
        self.time_date_y_position = 8
        self.time_date_small_y_position = 18


    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def deg_to_compass(self, degrees):
        """
        Convert numerical direction into the letters you'd see on a compas
        such as 'N' for north or 'SE' for south east.
        """
        val = int((degrees/22.5)+.5)
        dirs = ["N", "NNE", "NE", "ENE",
                "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW",
                "W", "WNW", "NW", "NNW"]
        return dirs[(val % 16)]

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
                    lang=self.config["lang"])

                sunset_today = datetime.datetime.fromtimestamp(
                    self.weather.daily[0].sunsetTime)
                if datetime.datetime.now() < sunset_today:
                    index = 0
                    sr_suffix = 'today'
                    ss_suffix = 'tonight'
                else:
                    index = 1
                    sr_suffix = 'tomorrow'
                    ss_suffix = 'tomorrow'

                self.sunrise = self.weather.daily[index].sunriseTime
                self.sunrise_string = datetime.datetime.fromtimestamp(
                    self.sunrise).strftime("%I:%M %p {}").format(sr_suffix)
                self.sunset = self.weather.daily[index].sunsetTime
                self.sunset_string = datetime.datetime.fromtimestamp(
                    self.sunset).strftime("%I:%M %p {}").format(ss_suffix)

            except requests.exceptions.RequestException as e:
                self.log.exception(f"Request exception: {e}")
                return False
            except AttributeError as e:
                self.log.exception(f"Attribute error: {e}")
                return False
        return True

    ####################################################################
    def string_print(self, text, font, x, line_number, text_color):
        """
        Prints a line of text on the display
        """
        rendered_font = font.render(text, True, text_color)
        self.screen.blit(rendered_font, (x, self.ymax * 0.075 * line_number))

    ####################################################################
    def disp_info(self, in_daylight, day_hrs, day_mins, seconds_til_daylight,
                  delta_seconds_til_dark):
        """
        Displays a screen providing information about this application
        along with the time of sunrise and sunset. The time and date are
        displayed in a different place than on the daily and hourly
        screens and there is no border. This is a conscious descison to
        help prevent screen burn-in.
        """
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (0, 0, 0)
        text_color = (255, 255, 255)
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line(self.screen, line_color,
                         (xmin, 0), (self.xmax, 0), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, 0), (xmin, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (self.xmax, 0), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines)

        time_height_large = self.time_date_text_height
        time_height_small = self.time_date_small_text_height

        # Time & Date
        regular_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_large), bold=1)
        small_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_small), bold=1)

        hours_and_minutes = time.strftime("%I:%M", time.localtime())
        am_pm = time.strftime(" %p", time.localtime())

        rendered_hours_and_minutes = regular_font.render(
            hours_and_minutes, True, text_color)
        (tx1, ty1) = rendered_hours_and_minutes.get_size()
        rendered_am_pm = small_font.render(am_pm, True, text_color)
        (tx2, ty2) = rendered_am_pm.get_size()

        tp = self.xmax / 2 - (tx1 + tx2) / 2
        self.screen.blit(rendered_hours_and_minutes,
                         (tp, self.time_date_y_position))
        self.screen.blit(rendered_am_pm,
                         (tp + tx1 + 3, self.time_date_small_y_position))

        self.string_print(
            "A weather rock powered by Dark Sky", small_font,
            self.xmax * 0.05, 3, text_color)

        self.string_print(
            "Sunrise: %s" % self.sunrise_string,
            small_font, self.xmax * 0.05, 4, text_color)

        self.string_print(
            "Sunset:  %s" % self.sunset_string,
            small_font, self.xmax * 0.05, 5, text_color)

        text = "Daylight: %d hrs %02d min" % (day_hrs, day_mins)
        self.string_print(text, small_font, self.xmax * 0.05, 6, text_color)

        # leaving row 7 blank

        if in_daylight:
            text = "Sunset in %d hrs %02d min" % utils.stot(
                delta_seconds_til_dark)
        else:
            text = "Sunrise in %d hrs %02d min" % utils.stot(
                seconds_til_daylight)
        self.string_print(text, small_font, self.xmax * 0.05, 8, text_color)

        # leaving row 9 blank

        text = "Weather checked at"
        self.string_print(text, small_font, self.xmax * 0.05, 10, text_color)

        text = "    %s" % time.strftime(
            "%I:%M:%S %p %Z on %a. %d %b %Y ",
            time.localtime(self.last_update_check))
        self.string_print(text, small_font, self.xmax * 0.05, 11, text_color)

        # Update the display
        pygame.display.update()

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap(self):
        pygame.image.save(self.screen, "screenshot.jpeg")
        self.log.info("Screen capture complete.")
