#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BEGIN LICENSE
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# END LICENSE

""" Fetches weather reports from Dark Sky for displaying on a screen. """

__version__ = "0.0.12"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################

# standard imports
import time
import datetime
import sys

# third party imports
from darksky import forecast
import requests
import pygame

# local imports
from weather_rock_methods import *

# global variable
UNICODE_DEGREE = u'\xb0'
log = get_logger()


def icon_mapping(icon, size):
    """
    https://darksky.net/dev/docs has this to say about icons:
    icon optional
    A machine-readable text summary of this data point, suitable for selecting
    an icon for display. If defined, this property will have one of the
    following values: clear-day, clear-night, rain, snow, sleet, wind, fog,
    cloudy, partly-cloudy-day, or partly-cloudy-night. (Developers should
    ensure that a sensible default is defined, as additional values, such as
    hail, thunderstorm, or tornado, may be defined in the future.)

    Based on that, this method will map the Dark Sky icon name to the name of
    an icon in this project.
    """
    if icon == 'clear-day':
        icon_path = 'icons/{}/clear.png'.format(size)
    elif icon == 'clear-night':
        icon_path = 'icons/{}/nt_clear.png'.format(size)
    elif icon == 'rain':
        icon_path = 'icons/{}/rain.png'.format(size)
    elif icon == 'snow':
        icon_path = 'icons/{}/snow.png'.format(size)
    elif icon == 'sleet':
        icon_path = 'icons/{}/sleet.png'.format(size)
    elif icon == 'wind':
        icon_path = 'icons/alt_icons/{}/wind.png'.format(size)
    elif icon == 'fog':
        icon_path = 'icons/{}/fog.png'.format(size)
    elif icon == 'cloudy':
        icon_path = 'icons/{}/cloudy.png'.format(size)
    elif icon == 'partly-cloudy-day':
        icon_path = 'icons/{}/partlycloudy.png'.format(size)
    elif icon == 'partly-cloudy-night':
        icon_path = 'icons/{}/nt_partlycloudy.png'.format(size)
    else:
        icon_path = 'icons/{}/unknown.png'.format(size)

    return icon_path


class Weather:
    def postpone(self, config, last_update_time):
        last_update_time += 300
        config["plugins"]["daily"]["last_update_time"] = last_update_time
        config["plugins"]["hourly"]["last_update_time"] = last_update_time

    def get_forecast(self, config):
        last_update_time = config["plugins"]["daily"]["last_update_time"]

        if (time.time() - last_update_time) > int(config["update_freq"]):
            log.info("Fetching update from DarkSky")
            try:
                self.weather = forecast(config["api_key"],
                                        config["lat"],
                                        config["lon"],
                                        exclude='minutely',
                                        units=config["units"],
                                        lang=config["lang"])

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

                # start with saying we don't need an umbrella
                self.take_umbrella = False
                icon_now = self.weather.icon
                icon_today = self.weather.daily[0].icon
                if icon_now == 'rain' or icon_today == 'rain':
                    self.take_umbrella = True
                else:
                    # determine if an umbrella is needed during daylight hours
                    curr_date = datetime.datetime.today().date()
                    for hour in self.weather.hourly:
                        hr = datetime.datetime.fromtimestamp(hour.time)
                        sr = datetime.datetime.fromtimestamp(
                            self.weather.daily[0].sunriseTime)
                        ss = datetime.datetime.fromtimestamp(
                            self.weather.daily[0].sunsetTime)
                        rain_chance = hour.precipProbability
                        is_today = hr.date() == curr_date
                        is_daylight_hr = hr >= sr and hr <= ss
                        if is_today and is_daylight_hr and rain_chance >= .25:
                            self.take_umbrella = True
                            break

                last_update_time = round(time.time())
                config["plugins"]["daily"]["last_update_time"] = (
                    last_update_time)
                config["plugins"]["hourly"]["last_update_time"] = (
                    last_update_time)

            except requests.exceptions.RequestException as e:
                log.debug('Request exception: %s' % e)
                if last_update_time != 0:
                    # If weather data has been retrieved at least once already.
                    self.postpone(config, last_update_time)
            except AttributeError as e:
                log.debug('Attribute error: %s' % e)
                if last_update_time != 0:
                    self.postpone(config, last_update_time)
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                log.debug("Decoding JSON has failed: %s" % sys.exc_info()[0])
                if last_update_time != 0:
                    self.postpone(config, last_update_time)
            except BaseException:
                log.debug("Unexpected error: %s" % sys.exc_info()[0])
                if last_update_time != 0:
                    self.postpone(config, last_update_time)

    def deg_to_compass(self, degrees):
        val = int((degrees/22.5)+.5)
        dirs = ["N", "NNE", "NE", "ENE",
                "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW",
                "W", "WNW", "NW", "NNW"]
        return dirs[(val % 16)]

    def units_decoder(self, units):
        """
        https://darksky.net/dev/docs has lists out what each
        unit is. The method below is just a codified version
        of what is on that page.
        """
        si_dict = {
            'nearestStormDistance': 'Kilometers',
            'precipIntensity': 'Millimeters per hour',
            'precipIntensityMax': 'Millimeters per hour',
            'precipAccumulation': 'Centimeters',
            'temperature': 'Degrees Celsius',
            'temperatureMin': 'Degrees Celsius',
            'temperatureMax': 'Degrees Celsius',
            'apparentTemperature': 'Degrees Celsius',
            'dewPoint': 'Degrees Celsius',
            'windSpeed': 'Meters per second',
            'windGust': 'Meters per second',
            'pressure': 'Hectopascals',
            'visibility': 'Kilometers',
        }
        ca_dict = si_dict.copy()
        ca_dict['windSpeed'] = 'Kilometers per hour'
        ca_dict['windGust'] = 'Kilometers per hour'
        uk2_dict = si_dict.copy()
        uk2_dict['nearestStormDistance'] = 'Miles'
        uk2_dict['visibility'] = 'Miles'
        uk2_dict['windSpeed'] = 'Miles per hour'
        uk2_dict['windGust'] = 'Miles per hour'
        us_dict = {
            'nearestStormDistance': 'Miles',
            'precipIntensity': 'Inches per hour',
            'precipIntensityMax': 'Inches per hour',
            'precipAccumulation': 'Inches',
            'temperature': 'Degrees Fahrenheit',
            'temperatureMin': 'Degrees Fahrenheit',
            'temperatureMax': 'Degrees Fahrenheit',
            'apparentTemperature': 'Degrees Fahrenheit',
            'dewPoint': 'Degrees Fahrenheit',
            'windSpeed': 'Miles per hour',
            'windGust': 'Miles per hour',
            'pressure': 'Millibars',
            'visibility': 'Miles',
        }
        switcher = {
            'ca': ca_dict,
            'uk2': uk2_dict,
            'us': us_dict,
            'si': si_dict,
        }
        return switcher.get(units, "Invalid unit name")

    def get_abbreviation(self, phrase):
        abbreviation = ''.join(item[0].lower() for item in phrase.split())
        return abbreviation

    def get_windspeed_abbreviation(self, config):
        return self.get_abbreviation(
            self.units_decoder(config["units"])['windSpeed'])

    def get_temperature_letter(self, config):
        return self.units_decoder(
            config["units"])['temperature'].split(' ')[-1][0].upper()

    def display_conditions_line(
            self, config, label, cond, is_temp, multiplier=None):
        y_start_position = 0.17
        line_spacing_gap = 0.065
        conditions_text_height = 0.05
        degree_symbol_height = 0.03
        degree_symbol_y_offset = 0.001
        x_start_position = 0.52
        second_column_x_start_position = 0.69
        text_color = (255, 255, 255)
        font_name = "freesans"

        if multiplier is None:
            y_start = y_start_position
        else:
            y_start = (y_start_position + line_spacing_gap * multiplier)

        conditions_font = pygame.font.SysFont(
            font_name, int(self.ymax * conditions_text_height), bold=1)

        txt = conditions_font.render(str(label), True, text_color)

        self.screen.blit(
            txt, (self.xmax * x_start_position, self.ymax * y_start))

        txt = conditions_font.render(str(cond), True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position,
                               self.ymax * y_start))

        if is_temp:
            txt_x = txt.get_size()[0]
            degree_font = pygame.font.SysFont(
                font_name, int(self.ymax * degree_symbol_height), bold=1)
            degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
            self.screen.blit(degree_txt, (
                self.xmax * second_column_x_start_position + txt_x * 1.01,
                self.ymax * (y_start + degree_symbol_y_offset)))
            degree_letter = conditions_font.render(
                self.get_temperature_letter(config), True, text_color)
            degree_letter_x = degree_letter.get_size()[0]
            self.screen.blit(degree_letter, (
                self.xmax * second_column_x_start_position +
                txt_x + degree_letter_x * 1.01,
                self.ymax * (y_start + degree_symbol_y_offset)))

    def display_subwindow(self, config, data, day, c_times):
        subwindow_centers = 0.125
        subwindows_y_start_position = 0.530
        line_spacing_gap = 0.065
        rain_percent_line_offset = 5.95
        rain_present_text_height = 0.060
        text_color = (255, 255, 255)
        font_name = "freesans"

        forecast_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.subwindow_text_height), bold=1)
        rpfont = pygame.font.SysFont(
            font_name, int(self.ymax * rain_present_text_height), bold=1)

        txt = forecast_font.render(day, True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax *
                               (subwindow_centers * c_times) - txt_x / 2,
                               self.ymax * (subwindows_y_start_position +
                                            line_spacing_gap * 0)))
        if hasattr(data, 'temperatureLow'):
            txt = forecast_font.render(
                str(int(round(data.temperatureHigh))) +
                UNICODE_DEGREE +
                ' / ' +
                str(int(round(data.temperatureLow))) +
                UNICODE_DEGREE + self.get_temperature_letter(config),
                True, text_color)
        else:
            txt = forecast_font.render(
                str(int(round(data.temperature))) +
                UNICODE_DEGREE + self.get_temperature_letter(config),
                True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax *
                               (subwindow_centers * c_times) - txt_x / 2,
                               self.ymax * (subwindows_y_start_position +
                                            line_spacing_gap * 5)))
        rptxt = rpfont.render(
            str(int(round(data.precipProbability * 100))) + '%',
            True, text_color)
        (txt_x, txt_y) = rptxt.get_size()
        self.screen.blit(rptxt, (self.xmax *
                                 (subwindow_centers * c_times) - txt_x / 2,
                                 self.ymax * (subwindows_y_start_position +
                                              line_spacing_gap *
                                              rain_percent_line_offset)))
        icon = pygame.image.load(
            icon_mapping(data.icon, self.icon_size)).convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = float(config["icon_offset"])

        self.screen.blit(icon, (self.xmax *
                                (subwindow_centers * c_times) -
                                icon_size_x / 2,
                                self.ymax *
                                (subwindows_y_start_position +
                                 line_spacing_gap
                                 * 1.2) + icon_y_offset))

    def disp_summary(self):
        y_start_position = 0.444
        conditions_text_height = 0.04
        text_color = (255, 255, 255)
        font_name = "freesans"

        conditions_font = pygame.font.SysFont(
            font_name, int(self.ymax * conditions_text_height), bold=1)
        txt = conditions_font.render(self.weather.summary, True, text_color)
        txt_x = txt.get_size()[0]
        x = self.xmax * 0.27 - (txt_x * 1.02) / 2
        self.screen.blit(txt, (x, self.ymax * y_start_position))

    def disp_umbrella_info(self, umbrella_txt):
        x_start_position = 0.52
        y_start_position = 0.444
        conditions_text_height = 0.04
        text_color = (255, 255, 255)
        font_name = "freesans"

        conditions_font = pygame.font.SysFont(
            font_name, int(self.ymax * conditions_text_height), bold=1)
        txt = conditions_font.render(umbrella_txt, True, text_color)
        self.screen.blit(txt, (
            self.xmax * x_start_position,
            self.ymax * y_start_position))

    def disp_current_temp(self, config, font_name, text_color):
        # Outside Temp
        outside_temp_font = pygame.font.SysFont(
            font_name, int(self.ymax * (0.5 - 0.15) * 0.6), bold=1)
        txt = outside_temp_font.render(
            str(int(round(self.weather.temperature))), True, text_color)
        (txt_x, txt_y) = txt.get_size()
        degree_font = pygame.font.SysFont(
            font_name, int(self.ymax * (0.5 - 0.15) * 0.3), bold=1)
        degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = degree_txt.get_size()
        degree_letter = outside_temp_font.render(
            self.get_temperature_letter(config), True, text_color)
        (degree_letter_x, degree_letter_y) = degree_letter.get_size()
        # Position text
        x = self.xmax * 0.27 - (txt_x * 1.02 + rendered_am_pm_x +
                                degree_letter_x) / 2
        self.screen.blit(txt, (x, self.ymax * 0.20))
        x = x + (txt_x * 1.02)
        self.screen.blit(degree_txt, (x, self.ymax * 0.2))
        x = x + (rendered_am_pm_x * 1.02)
        self.screen.blit(degree_letter, (x, self.ymax * 0.2))

    def draw_screen_border(self, line_color, xmin, lines):
        # Draw Screen Border
        # Top
        pygame.draw.line(self.screen, line_color, (xmin, 0), (self.xmax, 0),
                         lines)
        # Left
        pygame.draw.line(self.screen, line_color, (xmin, 0),
                         (xmin, self.ymax), lines)
        # Bottom
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax),
                         (self.xmax, self.ymax), lines)
        # Right
        pygame.draw.line(self.screen, line_color, (self.xmax, 0),
                         (self.xmax, self.ymax + 2), lines)
        # Bottom of top box
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines)
        # Bottom of middle box
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.5),
                         (self.xmax, self.ymax * 0.5), lines)
        # Bottom row, left vertical
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.25,
                                                   self.ymax * 0.5),
                         (self.xmax * 0.25, self.ymax), lines)
        # Bottom row, center vertical
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.5,
                                                   self.ymax * 0.15),
                         (self.xmax * 0.5, self.ymax), lines)
        # Bottom row, right vertical
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.75,
                                                   self.ymax * 0.5),
                         (self.xmax * 0.75, self.ymax), lines)

    # Given a sunrise and sunset unix timestamp,
    # return true if current local time is between sunrise and sunset. In
    # other words, return true if it's daytime and the sun is up. Also, return
    # the number of hours:minutes of daylight in this day. Lastly, return the
    # number of seconds until daybreak and sunset. If it's dark, daybreak is
    # set to the number of seconds until sunrise. If it daytime, sunset is set
    # to the number of seconds until the sun sets.
    #
    # So, five things are returned as:
    #  (InDaylight, Hours, Minutes, secToSun, secToDark).

    ##########################################################################
    def daylight(self, weather):
        inDaylight = False    # Default return code.

        # Get current datetime with tz's local day and time.
        tNow = datetime.datetime.now()

        # Build a datetime variable from a unix timestamp for today's sunrise.
        tSunrise = datetime.datetime.fromtimestamp(
            weather.daily[0].sunriseTime)
        tSunset = datetime.datetime.fromtimestamp(weather.daily[0].sunsetTime)

        # Test if current time is between sunrise and sunset.
        if (tNow > tSunrise) and (tNow < tSunset):
            inDaylight = True        # We're in Daytime
            delta_seconds_til_dark = tSunset - tNow
            seconds_til_daylight = 0
        else:
            inDaylight = False        # We're in Nighttime
            delta_seconds_til_dark = 0            # Seconds until dark.
            # Delta seconds until daybreak.
            if tNow > tSunset:
                # Must be evening - compute sunrise as time left today
                # plus time from midnight tomorrow.
                sunrise_tomorrow = datetime.datetime.fromtimestamp(
                    weather.daily[1].sunriseTime)
                seconds_til_daylight = sunrise_tomorrow - tNow
            else:
                # Else, must be early morning hours. Time to sunrise is
                # just the delta between sunrise and now.
                seconds_til_daylight = tSunrise - tNow

        # Compute the delta time (in seconds) between sunrise and set.
        dDaySec = tSunset - tSunrise        # timedelta in seconds
        (dayHrs, dayMin) = stot(dDaySec)    # split into hours and minutes.

        return (inDaylight, dayHrs, dayMin, seconds_til_daylight,
                delta_seconds_til_dark)
