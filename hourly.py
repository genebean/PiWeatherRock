#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BEGIN LICENSE

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
#   Raspberry Pi Weather Display Hourly Plugn
#   Original By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################

# local imports
import datetime


def update(my_disp):
    my_disp.get_forecast()


def disp(my_disp):
    # Fill the screen with black
    my_disp.screen.fill((0, 0, 0))
    xmin = 10
    lines = 5
    line_color = (255, 255, 255)
    text_color = (255, 255, 255)
    font_name = "freesans"

    my_disp.draw_screen_border(line_color, xmin, lines)
    my_disp.disp_header(font_name, text_color, 'time-date')
    my_disp.disp_current_temp(font_name, text_color)
    my_disp.disp_summary()
    my_disp.display_conditions_line('Feels Like:', int(round(
                                        my_disp.weather.apparentTemperature)),
                                    True)

    try:
        wind_bearing = my_disp.weather.windBearing
        wind_direction = my_disp.deg_to_compass(wind_bearing) + ' @ '
    except AttributeError:
        wind_direction = ''
    wind_txt = (wind_direction + str(int(round(my_disp.weather.windSpeed))) +
                " " + my_disp.get_windspeed_abbreviation())
    my_disp.display_conditions_line('Wind:', wind_txt, False, 1)

    my_disp.display_conditions_line('Humidity:', str(int(round((
                                        my_disp.weather.humidity * 100)))) +
                                    '%', False, 2)

    # Skipping multiplier 3 (line 4)

    if my_disp.take_umbrella:
        umbrella_txt = 'Grab your umbrella!'
    else:
        umbrella_txt = 'No umbrella needed today.'
    my_disp.disp_umbrella_info(umbrella_txt)

    # Current hour
    this_hour = my_disp.weather.hourly[0]
    this_hour_24_int = int(datetime.datetime.fromtimestamp(
        this_hour.time).strftime("%H"))
    if this_hour_24_int <= 11:
        ampm = 'a.m.'
    else:
        ampm = 'p.m.'
    this_hour_12_int = int(datetime.datetime.fromtimestamp(
        this_hour.time).strftime("%I"))
    this_hour_string = "{} {}".format(str(this_hour_12_int), ampm)
    multiplier = 1
    my_disp.display_subwindow(this_hour, this_hour_string, multiplier)

    # counts from 0 to 2
    for future_hour in range(3):
        this_hour = my_disp.weather.hourly[future_hour + 1]
        this_hour_24_int = int(datetime.datetime.fromtimestamp(
            this_hour.time).strftime("%H"))
        if this_hour_24_int <= 11:
            ampm = 'a.m.'
        else:
            ampm = 'p.m.'
        this_hour_12_int = int(datetime.datetime.fromtimestamp(
            this_hour.time).strftime("%I"))
        this_hour_string = "{} {}".format(str(this_hour_12_int), ampm)
        multiplier += 2
        my_disp.display_subwindow(this_hour, this_hour_string, multiplier)
