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
import os
import platform
import signal
import sys
import time

# third party imports
import pygame

# local imports
from weather_rock_methods import *
import weather
import daily
import hourly
import info
import speedtest
import rss


def lock_check():
    if os.path.exists(".lock"):
        with open(".lock", "r") as f:
            val = f.read()
        if val.strip() == "1":
            return True
        else:
            return False
    else:
        with open(".lock", "w") as f:
            f.write("0")
        return False


def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, exit_gracefully)


###############################################################################
class MyDisplay(weather.Weather):
    screen = None

    ####################################################################
    def __init__(self):
        self.config, self.default = load_config()
        self.log = get_logger()
        "Ininitializes a new pygame screen using the framebuffer"
        if platform.system() == 'Darwin':
            pygame.display.init()
            driver = pygame.display.get_driver()
            print('Using the {0} driver.'.format(driver))
            self.log.debug('Using the {0} driver.'.format(driver))
        else:
            # Based on "Python GUI in Linux frame buffer"
            # http://www.karoltomala.com/blog/?p=679
            # archived at https://web.archive.org/
            disp_no = os.getenv("DISPLAY")
            if disp_no:
                self.log.debug("X Display = {0}".format(disp_no))

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
                    self.log.debug('Driver: {0} failed.'.format(driver))
                    continue
                found = True
                break

            if not found:
                raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w,
                pygame.display.Info().current_h)
        self.log.debug("Framebuffer Size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()

        if self.config["fullscreen"] == "yes":
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
        self.start_time = round(time.time())

    def disp_header(self, font_name, text_color, text):
        if not text:
            return
        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)
        # Small Font for Seconds
        small_font = pygame.font.SysFont(
            font_name,
            int(self.ymax * self.time_date_small_text_height), bold=1)
        if text == 'time-date':
            time_string = time.strftime("%a, %b %d   %I:%M", time.localtime())
            am_pm_string = time.strftime(" %p", time.localtime())

            rendered_time_string = time_date_font.render(time_string, True,
                                                         text_color)
            (rendered_time_x,
             rendered_time_y) = rendered_time_string.get_size()
            rendered_am_pm_string = small_font.render(am_pm_string, True,
                                                      text_color)
            (rendered_am_pm_x,
             rendered_am_pm_y) = rendered_am_pm_string.get_size()

            full_time_string_x_position = (
                self.xmax / 2 - (rendered_time_x + rendered_am_pm_x) / 2)
            self.screen.blit(rendered_time_string, (
                full_time_string_x_position, self.time_date_y_position))
            self.screen.blit(
                rendered_am_pm_string,
                (full_time_string_x_position + rendered_time_x + 3,
                 self.time_date_small_y_position))
        else:
            rendered_header = time_date_font.render(text, True, text_color)
            (header_x, header_y) = rendered_header.get_size()
            if header_x > 0.9 * self.xmax:
                pad = self.xmax * 0.45
            else:
                pad = header_x / 2
            self.screen.blit(
                rendered_header,
                ((self.xmax / 2) - pad, self.time_date_y_position))

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap(self):
        # Create target Directory if don't exist
        save_dir = 'screenshots'
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        timestamp = time.strftime("%Y-%m-%dT%H.%M.%S", time.localtime())
        pygame.image.save(self.screen, f"{save_dir}{timestamp}.jpeg")
        self.log.info("Screen capture complete.")


while True:
    running = lock_check()
    if running:
        my_disp = MyDisplay()
        my_disp.log.info("Received signal to begin running.")
        mode = my_disp.default
        reset_counter(mode, my_disp)  # Update screen count variables
        info_screen_time_count = 0  # Seconds showing info screen
        non_info_screen_time_count = 0  # Seconds showing non-info screen
    else:
        pygame.quit()
        continue

    # Loads data from darksky.net into class variables.
    my_disp.log.info('Retreiving intial weather data')
    my_disp.get_forecast()

    if not my_disp.config["plugins"]['daily']['last_update_time']:
        my_disp.log.info('Error: no data from darksky.net.')
        running = False
    else:
        my_disp.log.info('Successfully retreived intial weather data.')

    active_screens = []
    # Fetch initial data for other plugins
    for plugin in my_disp.config["plugins"].keys():
        if my_disp.config["plugins"][plugin]["enabled"] == "yes":
            active_screens.append(plugin)
            if plugin != "daily" and plugin != "hourly":
                my_disp.log.info("Retreiving intial %s data" % plugin)
                eval(f"{plugin}.update(my_disp)")
                last_update_time = (
                    my_disp.config["plugins"][plugin]["last_update_time"])
                if last_update_time:
                    my_disp.log.info(
                        "Successfully retreived intial %s data" % plugin)
                else:
                    my_disp.log.info(
                        "Error retreiving intial %s data. It will be disabled."
                        % plugin)
                    active_screens.remove(plugin)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    while running:
        with open(".lock", "r") as f:
            val = f.read()
        if val.strip() == "0":
            my_disp.log.info(
                "Lock file has instructed the application to wait and listen.")
            running = False
            break

        # Look for and process keyboard events to change modes.
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # On 'q' or keypad enter key, quit the program.
                if ((event.key == pygame.K_KP_ENTER) or
                        (event.key == pygame.K_q)):
                    running = False
                # On 's' key, save a screen shot.
                elif event.key == pygame.K_s:
                    my_disp.screen_cap()
                else:
                    # On 'd' key, set mode to 'daily' weather mode
                    if event.key == pygame.K_d:
                        mode = 'daily'
                    # On 'i' key, set mode to 'info'.
                    elif event.key == pygame.K_i:
                        mode = 'info'
                    # on 'h' key, set mode to 'hourly' weather mode
                    elif event.key == pygame.K_h:
                        mode = 'hourly'
                    reset_counter(mode, my_disp)
                    info_screen_time_count = 0
                    non_info_screen_time_count = 0

        if mode not in my_disp.config["plugins"].keys():
            # Start counting the seconds that info screen is shown.
            non_info_screen_time_count = 0
            info_screen_time_count += 1
            # Switch to default plugin screen, after 'info_pause' seconds.
            if info_screen_time_count > int(my_disp.config["info_pause"]):
                mode = my_disp.default
                reset_counter(mode, my_disp)
                my_disp.log.info(
                    "Switched from INFO to %s "
                    "after showing INFO for %s seconds"
                    % (my_disp.default.upper(), info_screen_time_count))
        else:
            # Start counting the seconds that plugin screens are shown.
            info_screen_time_count = 0
            non_info_screen_time_count += 1
            # Update / Refresh the switching time after each second.
            switch_time = time_to_switch(my_disp)

            # Check to see if it's time to switch to info screen
            if non_info_screen_time_count > int(my_disp.config["info_delay"]):
                mode = 'info'
                my_disp.log.info("Switched to INFO screen at %s seconds"
                                 % non_info_screen_time_count)
            elif (non_info_screen_time_count % switch_time) == 0:
                new_screen = active_screens[((active_screens.index(mode) + 1) %
                                             len(active_screens))]
                my_disp.log.info(
                    "Switched from %s to %s at %s seconds" % (
                        '{:10}'.format(mode.upper()),
                        '{:10}'.format(new_screen.upper()),
                        '{:>4}'.format(non_info_screen_time_count)))
                mode = new_screen
                my_disp.config["plugins"][mode]['count'] += 1
        # Update the display and check for updates.
        eval(f"{mode}.disp(my_disp)")
        pygame.display.update()
        eval(f"{mode}.update(my_disp)")

        # Loop timer.
        pygame.time.wait(1000)

pygame.quit()
