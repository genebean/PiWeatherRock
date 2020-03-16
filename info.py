#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BEGIN LICENSE
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
#   Raspberry Pi Weather Display Info Screen Plugin
#   Original By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################

# standard imports
import time

# third party imports
import pygame

# local imports
from weather_rock_methods import *


def update(my_disp, config):
    return my_disp.get_forecast(config)


def sPrint(my_disp, text, font, x, line_number, text_color):
    rendered_font = font.render(text, True, text_color)
    my_disp.screen.blit(rendered_font, (x, my_disp.ymax * 0.075 * line_number))


def disp(my_disp, config):
    (in_daylight, day_hrs, day_mins, seconds_til_daylight,
        delta_seconds_til_dark) = my_disp.daylight(my_disp.weather)
    # Fill the screen with black
    my_disp.screen.fill((0, 0, 0))
    xmin = 10
    lines = 5
    line_color = (0, 0, 0)
    text_color = (255, 255, 255)
    font_name = "freesans"

    # Draw Screen Border
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, 0), (my_disp.xmax, 0), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, 0), (xmin, my_disp.ymax), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, my_disp.ymax), (my_disp.xmax, my_disp.ymax), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (my_disp.xmax, 0), (my_disp.xmax, my_disp.ymax), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, my_disp.ymax * 0.15),
                     (my_disp.xmax, my_disp.ymax * 0.15), lines)

    time_height_large = my_disp.time_date_text_height
    time_height_small = my_disp.time_date_small_text_height

    # Time & Date
    regular_font = pygame.font.SysFont(
        font_name, int(my_disp.ymax * time_height_large), bold=1)
    small_font = pygame.font.SysFont(
        font_name, int(my_disp.ymax * time_height_small), bold=1)

    hours_and_minutes = time.strftime("%I:%M", time.localtime())
    am_pm = time.strftime(" %p", time.localtime())

    rendered_hours_and_minutes = regular_font.render(
        hours_and_minutes, True, text_color)
    (tx1, ty1) = rendered_hours_and_minutes.get_size()
    rendered_am_pm = small_font.render(am_pm, True, text_color)
    (tx2, ty2) = rendered_am_pm.get_size()

    tp = my_disp.xmax / 2 - (tx1 + tx2) / 2
    my_disp.screen.blit(rendered_hours_and_minutes,
                        (tp, my_disp.time_date_y_position))
    my_disp.screen.blit(rendered_am_pm,
                        (tp + tx1 + 3, my_disp.time_date_small_y_position))

    sPrint(my_disp, "A weather rock powered by Dark Sky", small_font,
           my_disp.xmax * 0.05, 3, text_color)

    sPrint(my_disp, "Sunrise: %s" % my_disp.sunrise_string,
           small_font, my_disp.xmax * 0.05, 4, text_color)

    sPrint(my_disp, "Sunset:  %s" % my_disp.sunset_string,
           small_font, my_disp.xmax * 0.05, 5, text_color)

    text = "Daylight: %d hrs %02d min" % (day_hrs, day_mins)
    sPrint(my_disp, text, small_font, my_disp.xmax * 0.05, 6, text_color)

    # leaving row 7 blank

    if in_daylight:
        text = "Sunset in %d hrs %02d min" % stot(delta_seconds_til_dark)
    else:
        text = "Sunrise in %d hrs %02d min" % stot(seconds_til_daylight)
    sPrint(my_disp, text, small_font, my_disp.xmax * 0.05, 8, text_color)

    # leaving row 9 blank

    text = "Weather checked at"
    sPrint(my_disp, text, small_font, my_disp.xmax * 0.05, 10, text_color)

    text = "    %s" % time.strftime(
        "%I:%M:%S %p %Z on %a. %d %b %Y ",
        time.localtime(config["plugins"]["daily"]["last_update_time"]))
    sPrint(my_disp, text, small_font, my_disp.xmax * 0.05, 11, text_color)
