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

""" Fetches RSS data for displaying on a screen. """

__version__ = "0.0.12"

###############################################################################
#   Raspberry Pi Weather Display RSS Plugin
#   Original By: GitHub user metaMMA          2020-03-15
###############################################################################

# standard imports
import json
import time
import os
import glob
import math
import re

# third-part imports
import feedparser
import pygame


def update(my_disp):
    rss_config = my_disp.config["plugins"]["rss"]

    initial = False
    if rss_config["last_update_time"] == 0:
        initial = True
        # Make sure the rss directory exists.
        os.makedirs(
            os.path.join(os.getcwd(), "rss"), exist_ok=True)

    if ((time.time() - rss_config["last_update_time"]) >
            int(rss_config["update_freq"])):
        slot_count = int(rss_config["cols"]) * int(rss_config["rows"])
        feed_list = []
        for x in range(10):
            if rss_config["feeds"][f"{x+1}"]["enabled"] == "yes":
                feed_list.append(rss_config["feeds"][f"{x+1}"]["url"])
        feed_dict = {}
        error_count = 0
        for feed in feed_list:
            feed_dict[feed] = feedparser.parse(feed)
            if len(feed_dict[feed]['entries']) == 0:
                my_disp.log.info('Error accessing feed: %s.' % feed)
                error_count += 1
        if initial and error_count == len(feed_list):
            my_disp.log.info("Error accessing all RSS feeds.")
        elif error_count == len(feed_list):
            my_disp.log.info("Error accessing all RSS feeds. "
                             "Will try again in 5 minutes.")
            my_disp.config["plugins"]["rss"]["last_update_time"] = (
                round(time.time()) + 300)
        else:
            item_dict = {}
            for x in range(slot_count):
                item_dict[x] = {}

            available_items = 0
            for feed in feed_list:
                available_items += len(feed_dict[feed]['entries'])
            if available_items < slot_count:
                slot_count = available_items
            added_items = 0
            loop = -1
            while True:
                loop += 1
                for feed in feed_list:
                    try:
                        item_dict[added_items] = (
                            feed_dict[feed]['entries'][loop]['title'])
                    except IndexError:
                        continue
                    added_items += 1
                    if added_items >= slot_count:
                        break
                if added_items >= slot_count:
                    break
            with open(f"rss/{round(time.time())}.json", 'w') as f:
                json.dump(item_dict, f)
            my_disp.config["plugins"]["rss"]["last_update_time"] = (
                round(time.time()))

    # Remove old RSS info
    rss_dir = os.getcwd() + '/rss/'
    file_list = glob.glob(rss_dir + "*.json")
    file_list.sort(key=os.path.getctime)
    keep = file_list[-3:]  # always keep 3 most recent files
    for fname in os.listdir(rss_dir):
        full_path = os.path.join(rss_dir, fname)
        if full_path not in keep and os.path.exists(full_path):
            os.remove(full_path)


def disp(my_disp):
    rss_config = my_disp.config["plugins"]["rss"]
    # Fill the screen with black
    my_disp.screen.fill((0, 0, 0))

    # Get stored RSS info
    list_of_files = glob.glob('rss/*.json')
    list_of_files.sort(key=os.path.getctime)
    if (os.stat(list_of_files[-1:][0]).st_size > 0):
        with open(list_of_files[-1:][0], 'rb') as f:
            info = json.load(f)
    else:
        with open(list_of_files[-2:][0], 'rb') as f:
            info = json.load(f)
    # Determine header type
    if rss_config["show_header"] == "yes":
        if rss_config["header_type"] == 'custom':
            header = rss_config["custom_header"]
        else:
            header = 'time-date'
    else:
        header = False

    # Draw borders and header
    font_name = "freesans"
    line_color = (255, 255, 255)
    text_color = (255, 255, 255)
    xmin = 10
    lines = 5
    if header:
        col_height = 0.75
        col_start = 0.2
        my_disp.disp_header('freesans', (255, 255, 255), header)
        # Bottom of top box
        pygame.draw.line(my_disp.screen, line_color,
                         (xmin, my_disp.ymax * 0.15),
                         (my_disp.xmax, my_disp.ymax * 0.15), lines)
    else:
        col_height = 0.9
        col_start = 0.05
    # Top
    pygame.draw.line(my_disp.screen, line_color, (xmin, 0), (my_disp.xmax, 0),
                     lines)
    # Left
    pygame.draw.line(my_disp.screen, line_color, (xmin, 0),
                     (xmin, my_disp.ymax), lines)
    # Bottom
    pygame.draw.line(my_disp.screen, line_color, (xmin, my_disp.ymax),
                     (my_disp.xmax, my_disp.ymax), lines)
    # Right
    pygame.draw.line(my_disp.screen, line_color, (my_disp.xmax, 0),
                     (my_disp.xmax, my_disp.ymax + 2), lines)
    slot_height = (col_height / int(rss_config["rows"]))
    font = pygame.font.SysFont(font_name,
                               int(slot_height * 0.9 * my_disp.ymax), bold=1)

    slot_width = 0.9 / int(rss_config["cols"])

    filled_count = 0
    filled = {}
    for col in range(int(rss_config["cols"])):
        filled[col] = {}
        for row in range(int(rss_config["rows"])):
            filled[col][row] = 0
    col = 0
    row = 0

    while True:
        item_title = u'\u2022' + info[str(filled_count)]
        rendered_text = font.render(item_title, True, text_color)
        (text_x, text_y) = rendered_text.get_size()
        new_title2 = False
        if text_x > my_disp.xmax * slot_width:
            char_space = text_x / len(item_title)
            char_limit = math.floor((my_disp.xmax * slot_width) / char_space)
            if rss_config["wrap_text"] == "yes":
                it = re.finditer(
                                 r"(?<![A-Za-z])'(?![A-Za-z])|[\"\- ]",
                                 item_title[:char_limit])
                break_points = [m.start(0) for m in it]
                new_title = item_title[:break_points[-1]]
                new_title2 = item_title[break_points[-1]:]
                if len(new_title2) > (char_limit - 2):
                    new_title2 = "  " + new_title2[:char_limit - 5] + "..."
                else:
                    new_title2 = "  " + new_title2[:char_limit]
            else:
                new_title = item_title[:char_limit - 3] + "..."
                new_title2 = False
            rendered_text = font.render(new_title, True, text_color)
        my_disp.screen.blit(
            rendered_text, (int(my_disp.xmax * (0.05 + col * slot_width)),
                            int(my_disp.ymax *
                                (col_start + row * slot_height))))
        row += 1
        filled_count += 1
        if new_title2:
            rendered_text = font.render(new_title2, True, text_color)
            my_disp.screen.blit(
                rendered_text, (int(my_disp.xmax * (0.05 + col * slot_width)),
                                int(my_disp.ymax *
                                    (col_start + row * slot_height))))
            row += 1
            filled_count += 1
        if row >= int(rss_config["rows"]):
            row = 0
            col += 1
        if col == int(rss_config["cols"]):
            break
