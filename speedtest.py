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

""" Fetches speedtest data for displaying on a screen. """

__version__ = "0.0.12"

###############################################################################
#   Raspberry Pi Weather Display Speedtest Plugin
#   Original By: github user: metaMMA          2020-03-15
###############################################################################

# standard imports
import datetime
import os
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


def update(my_disp):
    log = my_disp.log
    speedtest_config = my_disp.config["plugins"]["speedtest"]
    last_update_time = speedtest_config["last_update_time"]
    # Determine if this is the first time fetching new speedtest results.
    initial = False
    if last_update_time == 0:
        initial = True

    if initial:
        # Make sure the speedtest directories exist.
        os.makedirs(
            os.path.join(os.getcwd(), "speedtest", "queue"),
            exist_ok=True)
        os.makedirs(
            os.path.join(
                os.getcwd(), "speedtest", "archive"),
            exist_ok=True)

    # Run speedtest on Pi and store the results in json format.
    if speedtest_config["local_test"] == "yes":
        if ((time.time() -
                last_update_time) > int(speedtest_config["update_freq"])):
            log.info("Running speedtest on Pi.")
            try:
                subprocess.call(["sh",
                                "./scripts/speedtest.sh"])
                my_disp.config["plugins"]["speedtest"]["last_update_time"] = round(
                    time.time())
            except:
                log.info("Error performing speedtest")
                if not initial:
                    log.info("Will try again in 5 minutes.")
                    my_disp.config["plugins"]["speedtest"]["last_update_time"] = (
                        round(time.time()) + 300)
    else:
        if initial:
            # Make sure speedtest results from mounted location exist
            list_of_files = glob.glob(
                'speedtest/queue/*.json')
            list_of_files.sort(key=os.path.getctime)
            try:
                if os.stat(list_of_files[-1:][0]).st_size > 0:
                    my_disp.config["plugins"]["speedtest"]["last_update_time"] = round(
                        time.time())
                elif os.stat(list_of_files[-2:][0]).st_size > 0:
                    my_disp.config["plugins"]["speedtest"]["last_update_time"] = round(
                        time.time())
                else:
                    log.info('No speedtest results found.')
            except IndexError:
                log.info('No speedtest results found.')

    if not initial:
        # Move or remove old test results
        src = os.getcwd() + '/speedtest/queue/'
        dst = os.getcwd() + '/speedtest/archive/'
        file_list = glob.glob(src + "*.json")
        file_list.sort(key=os.path.getctime)
        keep = file_list[-3:]  # always keep 3 most recent results in queue
        for fname in os.listdir(src):
            if os.path.join(src, fname) not in keep:
                if speedtest_config["archive"] == "yes":
                    src_fname = os.path.join(src, fname)
                    dst_fname = os.path.join(dst, fname)
                    shutil.move(src_fname, dst_fname)
                else:
                    if os.path.exists(src_fname):
                        os.remove(src_fname)


def disp(my_disp):
    speedtest_config = my_disp.config["plugins"]["speedtest"]
    # Fill the screen with black
    my_disp.screen.fill((0, 0, 0))
    xmin = 10
    lines = 5
    line_color = (255, 255, 255)
    text_color = (255, 255, 255)
    font_name = "freesans"

    # Get stored speedtest results
    list_of_files = glob.glob(
        'speedtest/queue/*.json')
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
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, 0), (my_disp.xmax, 0), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, 0), (xmin, my_disp.ymax), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, my_disp.ymax), (my_disp.xmax, my_disp.ymax),
                     lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (my_disp.xmax, 0), (my_disp.xmax, my_disp.ymax), lines)
    pygame.draw.line(my_disp.screen, line_color,
                     (xmin, my_disp.ymax * 0.15),
                     (my_disp.xmax, my_disp.ymax * 0.15), lines)
    # Bottom of top box
    pygame.draw.line(my_disp.screen, line_color, (xmin, my_disp.ymax * 0.15),
                     (my_disp.xmax, my_disp.ymax * 0.15), lines)
    # Top of bottom box
    pygame.draw.line(my_disp.screen, line_color, (xmin, my_disp.ymax * 0.85),
                     (my_disp.xmax, my_disp.ymax * 0.85), lines)
    # Center line
    pygame.draw.line(my_disp.screen, line_color,
                     (my_disp.xmax * 0.5, my_disp.ymax * 0.15),
                     (my_disp.xmax * 0.5, my_disp.ymax * 0.85), lines)

    # Draw date and time at top of screen
    my_disp.disp_header(font_name, text_color, 'time-date')

    # Draw ping at the bottom of the screen
    ping_font = pygame.font.SysFont(
        font_name, int(my_disp.ymax * 0.075), bold=1)
    text = ping_font.render('Ping: ' + "{0:.1f}".format(ping) + ' ms',
                            True, text_color)
    (text_x, text_y) = text.get_size()
    my_disp.screen.blit(text, (my_disp.xmax * 0.25 - text_x / 2,
                        my_disp.ymax * 0.8875))

    # Draw speedtest time at the bottom of the screen
    utc_dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    dt_obj = utc_dt.replace(
        tzinfo=datetime.timezone.utc).astimezone(tz=None)
    time_txt = ping_font.render('Tested at ' + datetime.datetime.strftime(
        dt_obj, "%I:%M "), True, text_color)
    (time_txt_x, time_txt_y) = time_txt.get_size()
    ampm_font = pygame.font.SysFont(
        font_name, int(my_disp.ymax * 0.05), bold=1)
    ampm_text = ampm_font.render(
        datetime.datetime.strftime(dt_obj, "%p"), True, text_color)
    (ampm_text_x, ampm_text_y) = ampm_text.get_size()
    my_disp.screen.blit(time_txt, ((my_disp.xmax * 0.75) - (time_txt_x / 2) -
                        (ampm_text_x / 2), my_disp.ymax * 0.8875))
    my_disp.screen.blit(
        ampm_text,
        ((my_disp.xmax * 0.75) + (time_txt_x / 2) - 2 * (ampm_text_x / 3),
            my_disp.ymax * 0.895))

    # Determine which download dial image to show
    st_dir = 'icons/speedtest/'
    dl_percent_float = (dl / int(speedtest_config["dl_speed"])) * 100
    dl_percent = math.floor(dl_percent_float / 5) * 5
    if int(speedtest_config["red_cutoff"]) >= dl_percent:
        if dl_percent == 0:
            dl_img = f"{st_dir}red/5.svg"
        else:
            dl_img = f"{st_dir}red/{dl_percent}.svg"
    elif int(speedtest_config["yellow_cutoff"]) >= dl_percent:
        dl_img = f"{st_dir}yellow/{dl_percent}.svg"
    elif dl_percent >= 125:
        dl_img = f"{st_dir}green/125.svg"
    else:
        dl_img = f"{st_dir}green/{dl_percent}.svg"

    # Determine which upload dial image to show
    ul_percent_float = (ul / int(speedtest_config["ul_speed"])) * 100
    ul_percent = math.floor(ul_percent_float / 5) * 5
    if int(speedtest_config["red_cutoff"]) >= ul_percent:
        ul_img = f"{st_dir}red/{ul_percent}.svg"
        if ul_percent == 0:
            ul_img = f"{st_dir}red/5.svg"
    elif int(speedtest_config["yellow_cutoff"]) >= ul_percent:
        ul_img = f"{st_dir}yellow/{ul_percent}.svg"
    elif ul_percent >= 125:
        ul_img = f"{st_dir}green/125.svg"
    else:
        ul_img = f"{st_dir}green/{ul_percent}.svg"

    # Display download and upload dial images
    dl_dial_svg = load_svg(dl_img, fit_to=(
        (my_disp.ymax * 0.6, my_disp.ymax * 0.6)))
    ul_dial_svg = load_svg(ul_img, fit_to=(
        (my_disp.ymax * 0.6, my_disp.ymax * 0.6)))
    dial_size = my_disp.ymax * 0.6
    dial_pad = ((my_disp.xmax / 2) - dial_size) / 2
    my_disp.screen.blit(dl_dial_svg, (dial_pad, my_disp.ymax * 0.2))
    my_disp.screen.blit(ul_dial_svg,
                        ((my_disp.xmax / 2) + dial_pad, my_disp.ymax * 0.2))

    # Display download and upload identifier icons
    dl_icon_svg = load_svg(f"{st_dir}download.svg",
                           fit_to=((my_disp.ymax * 0.1, my_disp.ymax * 0.1)))
    ul_icon_svg = load_svg(f"{st_dir}upload.svg",
                           fit_to=((my_disp.ymax * 0.1, my_disp.ymax * 0.1)))
    my_disp.screen.blit(dl_icon_svg, ((dial_pad / 2), my_disp.ymax * 0.7))
    my_disp.screen.blit(ul_icon_svg, ((my_disp.xmax / 2) + (dial_pad / 2),
                                      my_disp.ymax * 0.7))
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
        'freesans', int(my_disp.ymax * 0.12), bold=1)
    dl_text = speed_font.render(dl_str, True, (255, 255, 255))
    ul_text = speed_font.render(ul_str, True, (255, 255, 255))
    (dl_text_x, dl_text_y) = dl_text.get_size()
    (ul_text_x, ul_text_y) = ul_text.get_size()
    if speedtest_config["show_mbps"] == "yes":
        # Optionally display Mb/s and change location of DL and UL rate
        rate_font = pygame.font.SysFont(
            'freesans', int(my_disp.ymax * 0.08), bold=1)
        text = rate_font.render('Mb/s', True, (255, 255, 255))
        (text_x, text_y) = text.get_size()
        my_disp.screen.blit(text,
                            (dial_pad + (my_disp.ymax * 0.3) - (text_x / 2),
                             my_disp.ymax * 0.53))
        my_disp.screen.blit(text,
                            (dial_pad + (my_disp.ymax * 0.3) - (text_x / 2) +
                             (my_disp.xmax / 2), my_disp.ymax * 0.53))
        my_disp.screen.blit(
            dl_text, (dial_pad + (my_disp.ymax * 0.3) - (dl_text_x / 2),
                      my_disp.ymax * 0.39))
        my_disp.screen.blit(
            ul_text, (dial_pad + (my_disp.ymax * 0.3) - (ul_text_x / 2) +
                      (my_disp.xmax / 2), my_disp.ymax * 0.39))
    else:
        my_disp.screen.blit(
            dl_text, (dial_pad + (my_disp.ymax * 0.3) - (dl_text_x / 2),
                      my_disp.ymax * 0.44))
        my_disp.screen.blit(
            ul_text, (dial_pad + (my_disp.ymax * 0.3) - (ul_text_x / 2) +
                      (my_disp.xmax / 2), my_disp.ymax * 0.44))

    # Display UL and DL percentage
    if speedtest_config["show_percentage"] == "yes":
        percent_font = pygame.font.SysFont(
            'freesans', int(my_disp.ymax * 0.08), bold=1)
        symbol_font = pygame.font.SysFont(
            'freesans', int(my_disp.ymax * 0.05), bold=1)
        dlp_text = percent_font.render(str(round(dl_percent_float)),
                                       True, (255, 255, 255))
        ulp_text = percent_font.render(str(round(ul_percent_float)),
                                       True, (255, 255, 255))
        symbol_text = symbol_font.render("%", True, (255, 255, 255))
        (symbol_text_x, symbol_text_y) = symbol_text.get_size()
        (dlp_text_x, dlp_text_y) = dlp_text.get_size()
        (ulp_text_x, ulp_text_y) = ulp_text.get_size()
        my_disp.screen.blit(dlp_text,
                            ((my_disp.xmax / 2) - 3 * (dial_pad / 4) -
                             (dlp_text_x / 2) - (symbol_text_x / 2),
                             my_disp.ymax * 0.72))
        my_disp.screen.blit(symbol_text,
                            ((my_disp.xmax / 2) - 3 * (dial_pad / 4) +
                             (dlp_text_x / 2) - (symbol_text_x / 2),
                             my_disp.ymax * 0.725))
        my_disp.screen.blit(ulp_text, (my_disp.xmax - 3 * (dial_pad / 4) -
                                       (ulp_text_x / 2) - (symbol_text_x / 2),
                                       my_disp.ymax * 0.72))
        my_disp.screen.blit(symbol_text,
                            (my_disp.xmax - 3 * (dial_pad / 4) +
                             (ulp_text_x / 2) - (symbol_text_x / 2),
                             my_disp.ymax * 0.725))
