#!/usr/bin/python
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

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# END LICENSE

""" Fetches weather reports Weather Underground for display on small screens."""

__version__ = "0.0.10"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017
###############################################################################
# standard imports
import calendar
import datetime
#import json
import os
import platform
#import random
import string
import sys
import syslog
import time

# third party imports
import pygame
from pygame.locals import *
import requests
import serial

import config

from X10 import X10_Bright, X10_Off, X10_On, X10_SetClock, X10_Status

# Setup GPIO pin BCM GPIO04
if not platform.system() == 'Darwin':
    ENABLE_GPIO = True

    if platform.machine() == 'x86_64':
        import GPIOmock as GPIO
    else:
        import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # Next
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # Shutdown
else:
    ENABLE_GPIO = False

MOUSE_X, MOUSE_Y = 0, 0
MODE = 'w'               # Default to weather mode.

UNICODE_DEGREE = u'\xb0'


###############################################################################

# Small LCD Display.
class SmDisplay:
    screen = None

    ####################################################################
    def __init__(self):
        if platform.system() == 'Darwin':
            pygame.display.init()
            driver = pygame.display.get_driver()
            print 'Using the {0} driver.'.format(driver)
        else:
            "Ininitializes a new pygame screen using the framebuffer"
            # Based on "Python GUI in Linux frame buffer"
            # http://www.karoltomala.com/blog/?p=679
            disp_no = os.getenv("DISPLAY")
            if disp_no:
                print "X Display = {0}".format(disp_no)
                syslog.syslog("X Display = {0}".format(disp_no))

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
                    print 'Driver: {0} failed.'.format(driver)
                    syslog.syslog('Driver: {0} failed.'.format(driver))
                    continue
                found = True
                break

            if not found:
                raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w,
                pygame.display.Info().current_h)
        print "Framebuffer Size: %d x %d" % (size[0], size[1])
        syslog.syslog("Framebuffer Size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()
        # for fontname in pygame.font.get_fonts():
        #        print fontname
        self.temp = ''
        self.feels_like = 0
        self.wind_speed = 0
        self.baro = 0.0
        self.wind_dir = 'S'
        self.humid = 0
        self.last_update_check = ''
        self.observation_time = ''
        self.day = ['', '', '', '']
        self.icon = [0, 0, 0, 0]
        self.rain = ['', '', '', '']
        self.temps = [['', ''], ['', ''], ['', ''], ['', '']]
        self.sunrise = '7:00 AM'
        self.sunset = '8:00 PM'

        if config.FULLSCREEN:
            self.xmax = pygame.display.Info().current_w - 35
            self.ymax = pygame.display.Info().current_h - 5
            self.icon_folder = 'icons/256x256/'
        else:
            self.xmax = 480 - 35
            self.ymax = 320 - 5
            self.icon_folder = 'icons/64x64/'
        self.subwindow_text_height = 0.055
        self.time_date_text_height = 0.115
        self.time_date_small_text_height = 0.075
        self.time_date_y_position = 8
        self.time_date_small_y_position = 18

    ####################################################################
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    ####################################################################
    def update_weather(self):
        if (self.observation_time == '') or (time.time() -
                                             self.last_update_check > config.WU_CHECK_INTERVAL):
            self.last_update_check = time.time()

            # This is where the magic happens.
            url = 'http://api.wunderground.com/api/%s/alerts/astronomy/conditions/forecast/q/%s.json' % (
                config.WU_API_KEY, config.ZIP_CODE)
            self.weather = requests.get(url).json()
            current_observation = self.weather['current_observation']
            sun_phase = self.weather['sun_phase']
            moon_phase = self.weather['moon_phase']
            simple_forecast = self.weather['forecast']['simpleforecast']['forecastday']
            txt_forecast = self.weather['forecast']['txt_forecast']['forecastday']

            try:
                if (str(current_observation['observation_time_rfc822'])
                        != self.observation_time):
                    self.observation_time = str(current_observation['observation_time_rfc822'])
                    print "New Weather Update: " + self.observation_time
                    self.temp = str(current_observation['temp_f'])
                    self.feels_like = str(current_observation['feelslike_f'])
                    self.wind_speed = str(current_observation['wind_mph'])
                    self.baro = str(current_observation['pressure_in'])
                    self.wind_dir = str(current_observation['wind_dir'])
                    self.humid = str(current_observation['relative_humidity'])
                    self.vis = str(current_observation['visibility_mi'])
                    self.gust = str(current_observation['wind_gust_mph'])
                    self.wind_direction = str(current_observation['wind_dir'])
                    self.day[0] = str(simple_forecast[0]['date']['weekday'])
                    self.day[1] = str(simple_forecast[1]['date']['weekday'])
                    self.day[2] = str(simple_forecast[2]['date']['weekday'])
                    self.day[3] = str(simple_forecast[3]['date']['weekday'])
                    self.sunrise = "%s:%s" % (
                        sun_phase['sunrise']['hour'], sun_phase['sunrise']['minute'])
                    self.sunset = "%s:%s" % (
                        sun_phase['sunset']['hour'], sun_phase['sunset']['minute'])
                    self.icon[0] = str(simple_forecast[0]['icon'])
                    self.icon[1] = str(simple_forecast[1]['icon'])
                    self.icon[2] = str(simple_forecast[2]['icon'])
                    self.icon[3] = str(simple_forecast[3]['icon'])
                    print 'WU Icons: ', self.icon[0], self.icon[1], self.icon[2], self.icon[3]
                    # print 'File: ', sd+self.icon[0]]
                    self.rain[0] = str(simple_forecast[0]['pop'])
                    self.rain[1] = str(simple_forecast[1]['pop'])
                    self.rain[2] = str(simple_forecast[2]['pop'])
                    self.rain[3] = str(simple_forecast[3]['pop'])
                    self.temps[0][0] = str(
                        simple_forecast[0]['high']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[0][1] = str(
                        simple_forecast[0]['low']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[1][0] = str(
                        simple_forecast[1]['high']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[1][1] = str(
                        simple_forecast[1]['low']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[2][0] = str(
                        simple_forecast[2]['high']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[2][1] = str(
                        simple_forecast[2]['low']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[3][0] = str(
                        simple_forecast[3]['high']['fahrenheit']) + UNICODE_DEGREE
                    self.temps[3][1] = str(
                        simple_forecast[3]['low']['fahrenheit']) + UNICODE_DEGREE
            except KeyError:
                print "KeyError -> Weather Error"
                self.temp = '??'
                self.observation_time = ''
                return False
            # except ValueError:
            #    print "ValueError -> Weather Error"

        return True

    ####################################################################
    def disp_weather(self):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line(self.screen, line_color, (xmin, 0), (self.xmax, 0),
                         lines)                      # Top
        pygame.draw.line(self.screen, line_color, (xmin, 0),
                         (xmin, self.ymax), lines)        # Left
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax),
                         (self.xmax, self.ymax), lines)        # Bottom
        pygame.draw.line(self.screen, line_color, (self.xmax, 0),
                         (self.xmax, self.ymax + 2), lines)    # Right
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines) # Bottom of top box
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.5),
                         (self.xmax, self.ymax * 0.5), lines)  # Bottom of middle box
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.25, self.ymax * 0.5),
                         (self.xmax * 0.25, self.ymax), lines) # Bottom row, left vertical
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.5, self.ymax * 0.15),
                         (self.xmax * 0.5, self.ymax), lines)  # Bottom row, center vertical
        pygame.draw.line(self.screen, line_color, (self.xmax * 0.75, self.ymax * 0.5),
                         (self.xmax * 0.75, self.ymax), lines) # Bottom row, right vertical

        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)
        # Small Font for Seconds
        small_font = pygame.font.SysFont(font_name, int(self.ymax * self.time_date_small_text_height), bold=1)

        time_string = time.strftime("%a, %b %d   %I:%M", time.localtime())
        am_pm_string = time.strftime(" %p", time.localtime())

        rendered_time_string = time_date_font.render(time_string, True, text_color)
        (rendered_time_x, rendered_time_y) = rendered_time_string.get_size()
        rendered_am_pm_string = small_font.render(am_pm_string, True, text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = rendered_am_pm_string.get_size()

        full_time_string_x_position = self.xmax / 2 - (rendered_time_x + rendered_am_pm_x) / 2
        self.screen.blit(rendered_time_string, (full_time_string_x_position, self.time_date_y_position))
        self.screen.blit(rendered_am_pm_string, (full_time_string_x_position + rendered_time_x + 3, self.time_date_small_y_position))

        # Outside Temp
        outside_temp_font = pygame.font.SysFont(font_name, int(self.ymax * (0.5 - 0.15) * 0.6), bold=1)
        txt = outside_temp_font.render(self.temp, True, text_color)
        (txt_x, txt_y) = txt.get_size()
        # Show degree F symbol using magic unicode char in a smaller font size.
        degree_font = pygame.font.SysFont(font_name, int(self.ymax * (0.5 - 0.15) * 0.3), bold=1)
        degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = degree_txt.get_size()
        x = self.xmax * 0.27 - (txt_x * 1.02 + rendered_am_pm_x) / 2
        self.screen.blit(txt, (x, self.ymax * 0.20))
        #self.screen.blit(txt, (self.xmax*0.02,self.ymax*0.15))
        x = x + (txt_x * 1.02)
        self.screen.blit(degree_txt, (x, self.ymax * 0.2))
        #self.screen.blit(dtxt, (self.xmax*0.02+tx*1.02,self.ymax*0.2))

        # Conditions
        y_start_position = 0.17
        line_spacing_gap = 0.065
        conditions_text_height = 0.05
        degree_symbol_height = 0.03
        degree_symbol_y_offset = 0.001
        x_start_position = 0.52
        second_column_x_start_position = 0.73

        conditions_font = pygame.font.SysFont(font_name, int(self.ymax * conditions_text_height), bold=1)
        txt = conditions_font.render('Feels Like:', True, text_color)
        self.screen.blit(txt, (self.xmax * x_start_position, self.ymax * y_start_position))
        txt = conditions_font.render(self.feels_like, True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position, self.ymax * y_start_position))
        (txt_x, txt_y) = txt.get_size()
        # Show degree F symbol using magic unicode char.
        degree_font = pygame.font.SysFont(font_name, int(self.ymax * degree_symbol_height), bold=1)
        degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
        self.screen.blit(degree_txt, (self.xmax * second_column_x_start_position + txt_x * 1.01, self.ymax * (y_start_position + degree_symbol_y_offset)))

        txt = conditions_font.render('Currently:', True, text_color)
        self.screen.blit(txt, (self.xmax * x_start_position, self.ymax * (y_start_position + line_spacing_gap * 1)))
        txt = conditions_font.render(
            self.weather['current_observation']['weather'], True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position, self.ymax * (y_start_position + line_spacing_gap * 1)))

        txt = conditions_font.render('Windspeed:', True, text_color)
        self.screen.blit(txt, (self.xmax * x_start_position, self.ymax * (y_start_position + line_spacing_gap * 2)))
        txt = conditions_font.render(self.wind_speed + ' mph', True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position, self.ymax * (y_start_position + line_spacing_gap * 2)))

        txt = conditions_font.render('Direction:', True, text_color)
        self.screen.blit(txt, (self.xmax * x_start_position, self.ymax * (y_start_position + line_spacing_gap * 3)))
        txt = conditions_font.render(string.upper(self.wind_dir), True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position, self.ymax * (y_start_position + line_spacing_gap * 3)))

        txt = conditions_font.render('Humidity:', True, text_color)
        self.screen.blit(txt, (self.xmax * x_start_position, self.ymax * (y_start_position + line_spacing_gap * 4)))
        txt = conditions_font.render(self.humid, True, text_color)
        self.screen.blit(txt, (self.xmax * second_column_x_start_position, self.ymax * (y_start_position + line_spacing_gap * 4)))

        subwindow_centers = 0.125
        subwindows_y_start_position = 0.530
        rain_present_text_height = 0.060
        line_spacing_gap = 0.065
        rain_percent_line_offset = 5.95

        forecast_font = pygame.font.SysFont(font_name, int(self.ymax * self.subwindow_text_height), bold=1)
        rpfont = pygame.font.SysFont(font_name, int(self.ymax * rain_present_text_height), bold=1)

        # Sub Window 1
        txt = forecast_font.render('Today:', True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * subwindow_centers - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 0)))
        txt = forecast_font.render(self.temps[0][0] +
                                   ' / ' + self.temps[0][1], True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * subwindow_centers - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 5)))
        #rtxt = forecast_font.render('Rain:', True, lc)
        #self.screen.blit(rtxt, (ro,self.ymax*(wy+gp*5)))
        rptxt = rpfont.render(self.rain[0] + '%', True, text_color)
        (txt_x, txt_y) = rptxt.get_size()
        self.screen.blit(rptxt, (self.xmax * subwindow_centers - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * rain_percent_line_offset)))
        icon = pygame.image.load(
            self.icon_folder + self.icon[0] + '.png').convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = config.LARGE_ICON_OFFSET
        self.screen.blit(
            icon, (self.xmax * subwindow_centers - icon_size_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 1.2) + icon_y_offset))

        # Sub Window 2
        txt = forecast_font.render(self.day[1] + ':', True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * (subwindow_centers * 3) - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 0)))
        txt = forecast_font.render(self.temps[1][0] +
                                   ' / ' + self.temps[1][1], True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * subwindow_centers * 3 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 5)))
        #self.screen.blit(rtxt, (self.xmax*wx*2+ro,self.ymax*(wy+gp*5)))
        rptxt = rpfont.render(self.rain[1] + '%', True, text_color)
        (txt_x, txt_y) = rptxt.get_size()
        self.screen.blit(
            rptxt, (self.xmax * subwindow_centers * 3 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * rain_percent_line_offset)))
        icon = pygame.image.load(
            self.icon_folder + self.icon[1] + '.png').convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = config.LARGE_ICON_OFFSET
        self.screen.blit(icon, (self.xmax * subwindow_centers * 3 - icon_size_x / 2,
                                self.ymax * (subwindows_y_start_position + line_spacing_gap * 1.2) + icon_y_offset))

        # Sub Window 3
        txt = forecast_font.render(self.day[2] + ':', True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * (subwindow_centers * 5) - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 0)))
        txt = forecast_font.render(self.temps[2][0] +
                                   ' / ' + self.temps[2][1], True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * subwindow_centers * 5 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 5)))
        #self.screen.blit(rtxt, (self.xmax*wx*4+ro,self.ymax*(wy+gp*5)))
        rptxt = rpfont.render(self.rain[2] + '%', True, text_color)
        (txt_x, txt_y) = rptxt.get_size()
        self.screen.blit(
            rptxt, (self.xmax * subwindow_centers * 5 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * rain_percent_line_offset)))
        icon = pygame.image.load(
            self.icon_folder + self.icon[2] + '.png').convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = config.LARGE_ICON_OFFSET
        self.screen.blit(icon, (self.xmax * subwindow_centers * 5 - icon_size_x / 2,
                                self.ymax * (subwindows_y_start_position + line_spacing_gap * 1.2) + icon_y_offset))

        # Sub Window 4
        txt = forecast_font.render(self.day[3] + ':', True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * (subwindow_centers * 7) - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 0)))
        txt = forecast_font.render(self.temps[3][0] +
                                   ' / ' + self.temps[3][1], True, text_color)
        (txt_x, txt_y) = txt.get_size()
        self.screen.blit(txt, (self.xmax * subwindow_centers * 7 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * 5)))
        #self.screen.blit(rtxt, (self.xmax*wx*6+ro,self.ymax*(wy+gp*5)))
        rptxt = rpfont.render(self.rain[3] + '%', True, text_color)
        (txt_x, txt_y) = rptxt.get_size()
        self.screen.blit(
            rptxt, (self.xmax * subwindow_centers * 7 - txt_x / 2, self.ymax * (subwindows_y_start_position + line_spacing_gap * rain_percent_line_offset)))
        icon = pygame.image.load(
            self.icon_folder + self.icon[3] + '.png').convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = config.LARGE_ICON_OFFSET
        self.screen.blit(icon, (self.xmax * subwindow_centers * 7 - icon_size_x / 2,
                                self.ymax * (subwindows_y_start_position + line_spacing_gap * 1.2) + icon_y_offset))

        # Update the display
        pygame.display.update()

    ####################################################################
    def disp_calendar(self):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        small_font_name = "freemono"
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line(self.screen, line_color, (xmin, 0), (self.xmax, 0), lines)
        pygame.draw.line(self.screen, line_color, (xmin, 0), (xmin, self.ymax), lines)
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color, (self.xmax, 0), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines)

        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)          # Regular Font
        # Small Font for Seconds
        small_font = pygame.font.SysFont(font_name, int(self.ymax * self.time_date_small_text_height), bold=1)

        tm1 = time.strftime("%a, %b %d   %I:%M",
                            time.localtime())    # 1st part
        tm2 = time.strftime("%S", time.localtime())                   # 2nd
        tm3 = time.strftime(" %p", time.localtime())                  #

        rtm1 = time_date_font.render(tm1, True, line_color)
        (tx1, ty1) = rtm1.get_size()
        rtm2 = small_font.render(tm2, True, line_color)
        (tx2, ty2) = rtm2.get_size()
        rtm3 = time_date_font.render(tm3, True, line_color)
        (tx3, ty3) = rtm3.get_size()

        tp = self.xmax / 2 - (tx1 + tx2 + tx3) / 2
        self.screen.blit(rtm1, (tp, self.time_date_y_position))
        self.screen.blit(rtm2, (tp + tx1 + 3, self.time_date_small_y_position))
        self.screen.blit(rtm3, (tp + tx1 + tx2, self.time_date_y_position))

        # Conditions
        ys = 0.20        # Yaxis Start Pos
        xs = 0.20        # Xaxis Start Pos
        gp = 0.075       # Line Spacing Gap

        #cal = calendar.TextCalendar()
        yr = int(time.strftime("%Y", time.localtime()))    # Get Year
        mn = int(time.strftime("%m", time.localtime()))    # Get Month
        cal = calendar.month(yr, mn).splitlines()
        i = 0
        for cal_line in cal:
            txt = small_font.render(cal_line, True, line_color)
            self.screen.blit(txt, (self.xmax * xs, self.ymax * (ys + gp * i)))
            i = i + 1

        # Update the display
        pygame.display.update()

    ####################################################################
    def sPrint(self, text, font, x, line_number, text_color):
        rendered_font = font.render(text, True, text_color)
        self.screen.blit(rendered_font, (x, self.ymax * 0.075 * line_number))

    ####################################################################
    def disp_help(self, in_daylight, day_hrs, day_mins, seconds_til_daylight, delta_seconds_til_dark):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (0, 0, 0)
        text_color = (255, 255, 255)
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line(self.screen, line_color, (xmin, 0), (self.xmax, 0), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, 0), (xmin, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (self.xmax, 0), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax * 0.15), (self.xmax, self.ymax * 0.15), lines)

        time_height_large = self.time_date_text_height
        time_height_small = self.time_date_small_text_height

        # Time & Date
        regular_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_large), bold=1)
        small_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_small), bold=1)

        hours_and_minites = time.strftime("%I:%M", time.localtime())
        am_pm = time.strftime(" %p", time.localtime())

        rendered_hours_and_minutes = regular_font.render(
            hours_and_minites, True, text_color)
        (tx1, ty1) = rendered_hours_and_minutes.get_size()
        rendered_am_pm = small_font.render(am_pm, True, text_color)
        (tx2, ty2) = rendered_am_pm.get_size()

        tp = self.xmax / 2 - (tx1 + tx2) / 2
        self.screen.blit(rendered_hours_and_minutes, (tp, self.time_date_y_position))
        self.screen.blit(rendered_am_pm, (tp + tx1 + 3, self.time_date_small_y_position))

        self.sPrint("Sunrise: %s" % self.sunrise,
                    small_font, self.xmax * 0.05, 3, text_color)
        self.sPrint("Sunset: %s" % self.sunset,
                    small_font, self.xmax * 0.05, 4, text_color)

        text = "Daylight (Hrs:Min): %d:%02d" % (day_hrs, day_mins)
        self.sPrint(text, small_font, self.xmax * 0.05, 5, text_color)

        if in_daylight:
            text = "Sunset in (Hrs:Min): %d:%02d" % stot(delta_seconds_til_dark)
        else:
            text = "Sunrise in (Hrs:Min): %d:%02d" % stot(seconds_til_daylight)
        self.sPrint(text, small_font, self.xmax * 0.05, 6, text_color)

        text = ""
        self.sPrint(text, small_font, self.xmax * 0.05, 7, text_color)

        text = "Weather checked at"
        self.sPrint(text, small_font, self.xmax * 0.05, 8, text_color)

        text = "    %s" % time.strftime(
            "%a, %d %b %Y %H:%M:%S %Z", time.localtime(self.last_update_check))
        self.sPrint(text, small_font, self.xmax * 0.05, 9, text_color)

        text = "Weather observation time:"
        self.sPrint(text, small_font, self.xmax * 0.05, 10, text_color)

        text = "    %s" % self.observation_time
        self.sPrint(text, small_font, self.xmax * 0.05, 11, text_color)

        # Update the display
        pygame.display.update()

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap(self):
        pygame.image.save(self.screen, "screenshot.jpeg")
        print "Screen capture complete."


# Helper function to which takes seconds and returns (hours, minutes).
############################################################################
def stot(sec):
    min = sec.seconds // 60
    hrs = min // 60
    return (hrs, min % 60)


# Given a sunrise and sunset time string (sunrise example format '7:00 AM'),
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the
# number of seconds until sunrise. If it daytime, sunset is set to the number
# of seconds until the sun sets.
#
# So, five things are returned as:
#  (InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def Daylight(sr, st):
    inDaylight = False    # Default return code.

    # Get current datetime with tz's local day and time.
    tNow = datetime.datetime.now()

    # From a string like '7:00', build a datetime variable for
    # today with the hour and minute set to sunrise.
    t = time.strptime(sr, '%H:%M')        # Temp Var
    tSunrise = tNow                    # Copy time now.
    # Overwrite hour and minute with sunrise hour and minute.
    tSunrise = tSunrise.replace(hour=t.tm_hour, minute=t.tm_min, second=0)

    # From a string like '19:00', build a datetime variable for
    # today with the hour and minute set to sunset.
    t = time.strptime(myDisp.sunset, '%H:%M')
    tSunset = tNow                    # Copy time now.
    # Overwrite hour and minute with sunset hour and minute.
    tSunset = tSunset.replace(hour=t.tm_hour, minute=t.tm_min, second=0)

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
            tMidnight = tNow.replace(hour=23, minute=59, second=59)
            tNext = tNow.replace(hour=0, minute=0, second=0)
            seconds_til_daylight = (tMidnight - tNow) + (tSunrise - tNext)
        else:
            # Else, must be early morning hours. Time to sunrise is
            # just the delta between sunrise and now.
            seconds_til_daylight = tSunrise - tNow

    # Compute the delta time (in seconds) between sunrise and set.
    dDaySec = tSunset - tSunrise        # timedelta in seconds
    (dayHrs, dayMin) = stot(dDaySec)    # split into hours and minutes.

    return (inDaylight, dayHrs, dayMin, seconds_til_daylight, delta_seconds_til_dark)


############################################################################
def btnNext(channel):
    global MODE, non_weather_timeout, periodic_help_activation

    if MODE == 'c':
        MODE = 'w'
    elif MODE == 'w':
        MODE = 'h'
    elif MODE == 'h':
        MODE = 'c'

    non_weather_timeout = 0
    periodic_help_activation = 0

    print "Button Event!"


#==============================================================
#==============================================================

try:
    ser = serial.Serial("/dev/ttyUSB0", 4800, timeout=2)
    serActive = True
except BaseException:
    serActive = False
    print "Warning: can't open ttyUSB0 serial port."

if serActive:
    X10 = False        # Assume no X10 until proven wrong.
    ser.flushInput()    # Dump any junk that may be there.
    ser.flushOutput()

    ser.write(chr(0x8b))    # Querry Status
    c = ser.read(1)    # Wait for something from the CM11A.

    # If an attached CM11A sends a 0xA5 then it requirs a clock reset.
    if len(c) == 1:
        if ord(c) == 0xA5:
            X10_SetClock(ser)
    else:
        time.sleep(0.5)

    # Get the current status from the CM11A X10 module.
    (X10, c) = X10_Status(ser)

    if not X10:
        print 'Error: CM11A.'

    # If CM11A is present, turn on the lamp A3!
    if X10:
        if X10_On(ser, housecode['A'], unitcode['3']):
            print 'X10 On comand OK.'
        else:
            print 'Error in X10 On command.'
        time.sleep(2)
        if X10_Bright(ser, housecode['A'], unitcode['3']):
            print 'X10 Full Bright OK.'
        else:
            print 'Error in X10 Bright command.'

# exit()


# Display all the available fonts.
#print "Fonts: ", pygame.font.get_fonts()

MODE = 'w'        # Default to weather mode.

# Create an instance of the lcd display class.
myDisp = SmDisplay()

running = True             # Stay running while True
seconds = 0                # Seconds Placeholder to pace display.
# Display timeout to automatically switch back to weather dispaly.
non_weather_timeout = 0
periodic_help_activation = 0  # Switch to help periodically to prevent screen burn

# Loads data from Weather.com into class variables.
if myDisp.update_weather() == False:
    print 'Error: no data from Weather.com.'
    running = False

if ENABLE_GPIO:
    # Attach GPIO callback to our new button input on pin #4.
    GPIO.add_event_detect(4, GPIO.RISING, callback=btnNext, bouncetime=400)
    #GPIO.add_event_detect(17, GPIO.RISING, callback=btnShutdown, bouncetime=100)
    button_shutdown_count = 0

    if GPIO.input(17):
        print "Warning: Shutdown Switch is Active!"
        myDisp.screen.fill((0, 0, 0))
        icon = pygame.image.load('icons/64x64/' + 'shutdown.jpg')
        (ix, iy) = icon.get_size()
        myDisp.screen.blit(icon, (800 / 2 - ix / 2, 400 / 2 - iy / 2))
        gpio_font = pygame.font.SysFont("freesans", 40, bold=1)
        rf = gpio_font.render("Please toggle shutdown siwtch.", True, (255, 255, 255))
        (tx1, ty1) = rf.get_size()
        myDisp.screen.blit(rf, (800 / 2 - tx1 / 2, iy + 20))
        pygame.display.update()
        pygame.time.wait(1000)
        while GPIO.input(17):
            pygame.time.wait(100)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:

    if ENABLE_GPIO:
        # Debounce the shutdown switch. The main loop rnus at 100ms. So, if the
        # button (well, a switch really) counter "btnShutdownCnt" counts above
        # 25 then the switch must have been on continuously for 2.5 seconds.
        if GPIO.input(17):
            button_shutdown_count += 1
            if button_shutdown_count > 25:
                print "Shutdown!"
                myDisp.screen.fill((0, 0, 0))
                icon = pygame.image.load('icons/64x64/' + 'shutdown.jpg')
                (ix, iy) = icon.get_size()
                myDisp.screen.blit(icon, (800 / 2 - ix / 2, 400 / 2 - iy / 2))
                shutdown_button_font = pygame.font.SysFont("freesans", 60, bold=1)
                rtm1 = shutdown_button_font.render("Shuting Down!", True, (255, 255, 255))
                (tx1, ty1) = rtm1.get_size()
                myDisp.screen.blit(rtm1, (800 / 2 - tx1 / 2, iy + 20))
                pygame.display.update()
                pygame.time.wait(1000)
                #os.system("sudo shutdown -h now")
                while GPIO.input(17):
                    pygame.time.wait(100)
        else:
            button_shutdown_count = 0

    # Look for and process keyboard events to change modes.
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            # On 'q' or keypad enter key, quit the program.
            if ((event.key == K_KP_ENTER) or (event.key == K_q)):
                running = False

            # On 'c' key, set mode to 'calendar'.
            elif event.key == K_c:
                MODE = 'c'
                non_weather_timeout = 0
                periodic_help_activation = 0

            # On 'w' key, set mode to 'weather'.
            elif event.key == K_w:
                MODE = 'w'
                non_weather_timeout = 0
                periodic_help_activation = 0

            # On 's' key, save a screen shot.
            elif event.key == K_s:
                myDisp.screen_cap()

            # On 'h' key, set mode to 'help'.
            elif event.key == K_h:
                MODE = 'h'
                non_weather_timeout = 0
                periodic_help_activation = 0

    # Automatically switch back to weather display after a couple minutes.
    if MODE != 'w':
        periodic_help_activation = 0
        non_weather_timeout += 1
        if non_weather_timeout > 3000:    # Five minute timeout at 100ms loop rate.
            MODE = 'w'
            syslog.syslog("Switched to weather mode")
    else:
        non_weather_timeout = 0
        periodic_help_activation += 1
        if periodic_help_activation > 9000:  # 15 minute timeout at 100ms loop rate
            MODE = 'h'
            syslog.syslog("Switched to help mode")

    # Calendar Display Mode
    if MODE == 'c':
        # Update / Refresh the display after each second.
        if seconds != time.localtime().tm_sec:
            seconds = time.localtime().tm_sec
            myDisp.disp_calendar()

    # Weather Display Mode
    if MODE == 'w':
        # Update / Refresh the display after each second.
        if seconds != time.localtime().tm_sec:
            seconds = time.localtime().tm_sec
            myDisp.disp_weather()
            # ser.write("Weather\r\n")
        # Once the screen is updated, we have a full second to get the weather.
        # Once per minute, update the weather from the net.
        if seconds == 0:
            try:
                myDisp.update_weather()
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except BaseException:
                print("Unexpected error:", sys.exc_info()[0])

    if MODE == 'h':
        # Pace the screen updates to once per second.
        if seconds != time.localtime().tm_sec:
            seconds = time.localtime().tm_sec

            (inDaylight, dayHrs, dayMins, seconds_til_daylight, delta_seconds_til_dark) = Daylight(
                myDisp.sunrise, myDisp.sunset)

            # if inDaylight:
            #    print "Time until dark (Hr:Min) -> %d:%d" % stot(delta_seconds_til_dark)
            # else:
            #    #print 'seconds_til_daylight ->', seconds_til_daylight
            #    print "Time until daybreak (Hr:Min) -> %d:%d" % stot(seconds_til_daylight)

            # Stat Screen Display.
            myDisp.disp_help(inDaylight, dayHrs, dayMins, seconds_til_daylight, delta_seconds_til_dark)
        # Refresh the weather data once per minute.
        if int(seconds) == 0:
            try:
                myDisp.update_weather()
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except BaseException:
                print("Unexpected error:", sys.exc_info()[0])

    (inDaylight, dayHrs, dayMins, seconds_til_daylight, delta_seconds_til_dark) = Daylight(
        myDisp.sunrise, myDisp.sunset)

    if serActive:
        h = housecode['A']
        u = unitcode['3']

        if time.localtime().tm_sec == 30:
            if inDaylight is False:
                X10_On(ser, h, u)
                print "X10 On"
            else:
                X10_Off(ser, h, u)
                print "X10 Off"
        if time.localtime().tm_sec == 40:
            if inDaylight is False:
                X10_Bright(ser, housecode['A'], unitcode['3'])

    # Loop timer.
    pygame.time.wait(100)


pygame.quit()
