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

""" Fetches weather reports from Dark Sky for displaying on a screen.
    Plugin fetches network stats for displaying on a screen. """

__version__ = "0.0.12"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################

# standard imports
import datetime
import os
import syslog
import time
import subprocess
import math
import json
import glob
import shutil

# third party imports
import pygame

# local imports
from weather_rock_methods import *
import plugin_configs.speedtest_config as speedtest_config


class Speedtest:
    def get_speedtest(self, last_update_time):

        # Determine if this is the first time fetching new speedtest results.
        initial = False
        if last_update_time == 0:
            initial = True

        if initial:
            # Make sure the speedtest directories exist.
            os.makedirs(
                os.path.join("/home/pi/PiWeatherRock/", "speedtest", "queue"),
                exist_ok=True)
            os.makedirs(
                os.path.join(
                    "/home/pi/PiWeatherRock/", "speedtest", "archive"),
                exist_ok=True)

        # Run speedtest on Pi and store the results in json format.
        if speedtest_config.SPEEDTEST_ON_PI:
            if ((time.time() -
                 last_update_time) > speedtest_config.UPDATE_FREQ):
                last_update_time = round(time.time())
                syslog.syslog('Running speedtest on Pi.')
                subprocess.Popen(["/bin/bash",
                                  "/home/pi/PiWeatherRock/scripts/speedtest.sh"])
                if initial:
                    return last_update_time
        else:
            if initial:
                # Make sure speedtest results from mounted location exist
                list_of_files = glob.glob(
                    '/home/pi/PiWeatherRock/speedtest/queue/*.json')
                list_of_files.sort(key=os.path.getctime)
                if (os.stat(list_of_files[-1:][0]).st_size > 0 or
                        os.stat(list_of_files[-2:][0]).st_size > 0):
                    return round(time.time())
                else:
                    syslog.syslog('No speedtest results found.')
                    return False

        # Move or remove old test results
        src = '/home/pi/PiWeatherRock/speedtest/queue/'
        dst = '/home/pi/PiWeatherRock/speedtest/archive/'
        file_list = glob.glob(src + "*.json")
        file_list.sort(key=os.path.getctime)
        keep = file_list[-3:]  # always keep 3 most recent results in queue
        for fname in os.listdir(src):
            if os.path.join(src, fname) not in keep:
                if speedtest_config.KEEP_ALL_SPEEDTESTS:
                    src_fname = os.path.join(src, fname)
                    dst_fname = os.path.join(dst, fname)
                    shutil.move(src_fname, dst_fname)
                else:
                    if os.path.exists(src_fname):
                        os.remove(src_fname)

        return last_update_time

    def disp_speedtest(self, last_update_time):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        font_name = "freesans"

        # Get stored speedtest results
        list_of_files = glob.glob(
            '/home/pi/PiWeatherRock/speedtest/queue/*.json')
        list_of_files.sort(key=os.path.getctime)
        if (os.stat(list_of_files[-1:][0]).st_size > 0):
            with open(list_of_files[-1:][0], 'rb') as f:
                info = json.load(f)
        else:
            with open(list_of_files[-2:][0], 'rb') as f:
                info = json.load(f)

        ping = info['ping']
        dl = info['download'] / 1000000
        ul = info['upload'] / 1000000
        ts = info['timestamp']

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
        # Bottom of top box
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines)
        # Top of bottom box
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.85),
                         (self.xmax, self.ymax * 0.85), lines)
        # Center line
        pygame.draw.line(self.screen, line_color,
                         (self.xmax * 0.5, self.ymax * 0.15),
                         (self.xmax * 0.5, self.ymax * 0.85), lines)

        # Draw date and time at top of screen
        self.disp_time_date(font_name, text_color)

        # Draw ping at the bottom of the screen
        ping_font = pygame.font.SysFont(
            font_name, int(self.ymax * 0.075), bold=1)
        text = ping_font.render('Ping: ' + "{0:.1f}".format(ping) + ' ms',
                                True, text_color)
        (text_x, text_y) = text.get_size()
        self.screen.blit(text, (self.xmax * 0.25 - text_x / 2,
                                self.ymax * 0.8875))

        # Draw speedtest time at the bottom of the screen
        utc_dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt_obj = utc_dt.replace(
            tzinfo=datetime.timezone.utc).astimezone(tz=None)
        time_txt = ping_font.render('Tested at ' + datetime.datetime.strftime(
            dt_obj, "%I:%M "), True, text_color)
        (time_txt_x, time_txt_y) = time_txt.get_size()
        ampm_font = pygame.font.SysFont(
            font_name, int(self.ymax * 0.05), bold=1)
        ampm_text = ampm_font.render(
            datetime.datetime.strftime(dt_obj, "%p"), True, text_color)
        (ampm_text_x, ampm_text_y) = ampm_text.get_size()
        self.screen.blit(time_txt, ((self.xmax * 0.75) - (time_txt_x / 2) -
                                    (ampm_text_x / 2), self.ymax * 0.8875))
        self.screen.blit(
            ampm_text,
            ((self.xmax * 0.75) + (time_txt_x / 2) - 2 * (ampm_text_x / 3),
             self.ymax * 0.895))

        # Determine which download dial image to show
        st_dir = '/home/pi/PiWeatherRock/icons/speedtest/'
        dl_percent_float = (dl / speedtest_config.PROMISED_DL_SPEED) * 100
        dl_percent = math.floor(dl_percent_float / 5) * 5
        if speedtest_config.RED_CUTOFF >= dl_percent:
            if dl_percent == 0:
                dl_img = f"{st_dir}red/5.svg"
            else:
                dl_img = f"{st_dir}red/{dl_percent}.svg"
        elif speedtest_config.YELLOW_CUTOFF >= dl_percent:
            dl_img = f"{st_dir}yellow/{dl_percent}.svg"
        elif dl_percent >= 125:
            dl_img = f"{st_dir}green/125.svg"
        else:
            dl_img = f"{st_dir}green/{dl_percent}.svg"

        # Determine which upload dial image to show
        ul_percent_float = (ul / speedtest_config.PROMISED_UL_SPEED) * 100
        ul_percent = math.floor(ul_percent_float / 5) * 5
        if speedtest_config.RED_CUTOFF >= ul_percent:
            ul_img = f"{st_dir}red/{ul_percent}.svg"
            if ul_percent == 0:
                ul_img = f"{st_dir}red/5.svg"
        elif speedtest_config.YELLOW_CUTOFF >= ul_percent:
            ul_img = f"{st_dir}yellow/{ul_percent}.svg"
        elif ul_percent >= 125:
            ul_img = f"{st_dir}green/125.svg"
        else:
            ul_img = f"{st_dir}green/{ul_percent}.svg"

        # Display download and upload dial images
        dl_dial_svg = load_svg(dl_img, fit_to=(
            (self.ymax * 0.6, self.ymax * 0.6)))
        ul_dial_svg = load_svg(ul_img, fit_to=(
            (self.ymax * 0.6, self.ymax * 0.6)))
        dial_size = self.ymax * 0.6
        dial_pad = ((self.xmax / 2) - dial_size) / 2
        self.screen.blit(dl_dial_svg, (dial_pad, self.ymax * 0.2))
        self.screen.blit(ul_dial_svg,
                         ((self.xmax / 2) + dial_pad, self.ymax * 0.2))

        # Display download and upload identifier icons
        dl_icon_svg = load_svg(f"{st_dir}download.svg",
                               fit_to=((self.ymax * 0.1, self.ymax * 0.1)))
        ul_icon_svg = load_svg(f"{st_dir}upload.svg",
                               fit_to=((self.ymax * 0.1, self.ymax * 0.1)))
        self.screen.blit(dl_icon_svg, ((dial_pad / 2), self.ymax * 0.7))
        self.screen.blit(ul_icon_svg, ((self.xmax / 2) + (dial_pad / 2),
                                       self.ymax * 0.7))

        # Format the upload and download rate numbers depending on size
        if ul < 10:
            ul_str = "{0:.2f}".format(ul)
        elif 10 <= ul < 100:
            ul_str = "{0:.1f}".format(ul)
        else:
            ul_str = str(round(ul))

        if dl < 10:
            dl_str = "{0:.2f}".format(dl)
        elif 10 <= dl < 100:
            dl_str = "{0:.1f}".format(dl)
        else:
            dl_str = str(round(dl))

        # Display DL and UL rate in center of dial
        speed_font = pygame.font.SysFont(
            'freesans', int(self.ymax * 0.12), bold=1)
        dl_text = speed_font.render(dl_str, True, (255, 255, 255))
        ul_text = speed_font.render(ul_str, True, (255, 255, 255))
        (dl_text_x, dl_text_y) = dl_text.get_size()
        (ul_text_x, ul_text_y) = ul_text.get_size()
        if speedtest_config.SHOW_MBPS:
            # Optionally display Mb/s and change location of DL and UL rate
            rate_font = pygame.font.SysFont(
                'freesans', int(self.ymax * 0.08), bold=1)
            text = rate_font.render('Mb/s', True, (255, 255, 255))
            (text_x, text_y) = text.get_size()
            self.screen.blit(text,
                             (dial_pad + (self.ymax * 0.3) - (text_x / 2),
                              self.ymax * 0.53))
            self.screen.blit(text,
                             (dial_pad + (self.ymax * 0.3) - (text_x / 2) +
                              (self.xmax / 2), self.ymax * 0.53))
            self.screen.blit(
                dl_text, (dial_pad + (self.ymax * 0.3) - (dl_text_x / 2),
                          self.ymax * 0.39))
            self.screen.blit(
                ul_text, (dial_pad + (self.ymax * 0.3) - (ul_text_x / 2) +
                          (self.xmax / 2), self.ymax * 0.39))
        else:
            self.screen.blit(
                dl_text, (dial_pad + (self.ymax * 0.3) - (dl_text_x / 2),
                          self.ymax * 0.44))
            self.screen.blit(
                ul_text, (dial_pad + (self.ymax * 0.3) - (ul_text_x / 2) +
                          (self.xmax / 2), self.ymax * 0.44))

        # Display UL and DL percentage
        if speedtest_config.SHOW_SPEEDTEST_PERCENTAGE:
            percent_font = pygame.font.SysFont(
                'freesans', int(self.ymax * 0.08), bold=1)
            symbol_font = pygame.font.SysFont(
                'freesans', int(self.ymax * 0.05), bold=1)
            dlp_text = percent_font.render(str(round(dl_percent_float)),
                                           True, (255, 255, 255))
            ulp_text = percent_font.render(str(round(ul_percent_float)),
                                           True, (255, 255, 255))
            symbol_text = symbol_font.render("%", True, (255, 255, 255))
            (symbol_text_x, symbol_text_y) = symbol_text.get_size()
            (dlp_text_x, dlp_text_y) = dlp_text.get_size()
            (ulp_text_x, ulp_text_y) = ulp_text.get_size()
            self.screen.blit(dlp_text,
                             ((self.xmax / 2) - 3 * (dial_pad / 4) -
                              (dlp_text_x / 2) - (symbol_text_x / 2),
                              self.ymax * 0.72))
            self.screen.blit(symbol_text,
                             ((self.xmax / 2) - 3 * (dial_pad / 4) +
                              (dlp_text_x / 2) - (symbol_text_x / 2),
                              self.ymax * 0.725))
            self.screen.blit(
                ulp_text, (self.xmax - 3 * (dial_pad / 4) - (ulp_text_x / 2)
                           - (symbol_text_x / 2), self.ymax * 0.72))
            self.screen.blit(symbol_text,
                             (self.xmax - 3 * (dial_pad / 4) + (ulp_text_x / 2)
                              - (symbol_text_x / 2), self.ymax * 0.725))

        # Update the display
        pygame.display.update()
