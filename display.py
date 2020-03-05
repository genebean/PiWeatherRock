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
import syslog
import time

# third party imports
import pygame

# local imports
import config
import plugin_configs.info_config as info_config
from weather_rock_methods import *

from info import *
sys.path.insert(0, './plugin_configs')
for plugin in config.PLUGINS:
    exec(plugin + "_config = __import__(plugin + '_config')")
    exec("from " + plugin + " import *")

# globals
screen_info = {}
for plugin in config.PLUGINS:
    screen_info[plugin] = {}
    screen_info[plugin]['count'] = 0
    screen_info[plugin]['pause'] = eval(plugin + '_config.PAUSE')
    screen_info[plugin]['last_update_time'] = 0
mode = 'daily'  # Default to weather mode. Showing daily weather first.
reset_counter(mode, screen_info)  # Update screen count variables
running = True             # Stay running while True
seconds = 0                # Seconds placeholder to pace display.
info_screen_time_count = 0  # Time counter to trigger switch to non-info screen
non_info_screen_time_count = 0  # Time counter to trigger switch to info screen


def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, exit_gracefully)


###############################################################################
class MyDisplay:
    screen = None

    ####################################################################
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        if platform.system() == 'Darwin':
            pygame.display.init()
            driver = pygame.display.get_driver()
            print('Using the {0} driver.'.format(driver))
        else:
            # Based on "Python GUI in Linux frame buffer"
            # http://www.karoltomala.com/blog/?p=679
            # archived at https://web.archive.org/
            disp_no = os.getenv("DISPLAY")
            if disp_no:
                print("X Display = {0}".format(disp_no))
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
                    print('Driver: {0} failed.'.format(driver))
                    syslog.syslog('Driver: {0} failed.'.format(driver))
                    continue
                found = True
                break

            if not found:
                raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w,
                pygame.display.Info().current_h)
        print("Framebuffer Size: %d x %d" % (size[0], size[1]))
        syslog.syslog("Framebuffer Size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()

        if config.FULLSCREEN:
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

    def disp_time_date(self, font_name, text_color):
        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)
        # Small Font for Seconds
        small_font = pygame.font.SysFont(
            font_name,
            int(self.ymax * self.time_date_small_text_height), bold=1)

        time_string = time.strftime("%a, %b %d   %I:%M", time.localtime())
        am_pm_string = time.strftime(" %p", time.localtime())

        rendered_time_string = time_date_font.render(time_string, True,
                                                     text_color)
        (rendered_time_x, rendered_time_y) = rendered_time_string.get_size()
        rendered_am_pm_string = small_font.render(am_pm_string, True,
                                                  text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = rendered_am_pm_string.get_size()

        full_time_string_x_position = self.xmax / 2 - (rendered_time_x +
                                                       rendered_am_pm_x) / 2
        self.screen.blit(rendered_time_string, (full_time_string_x_position,
                                                self.time_date_y_position))
        self.screen.blit(rendered_am_pm_string,
                         (full_time_string_x_position + rendered_time_x + 3,
                          self.time_date_small_y_position))

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap(self):
        # Create target Directory if don't exist
        save_dir = '/home/pi/Pictures/PiWeatherRock/'
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        timestamp = time.strftime("%Y-%m-%dT%H.%M.%S", time.localtime())
        pygame.image.save(self.screen, f"{save_dir}{timestamp}.jpeg")
        print("Screen capture complete.")


# Create an instance of the lcd display class.
my_disp = MyDisplay()

# Extend my_disp to use methods from all active plugin classes
all_screens = list(screen_info.keys())
all_screens.append('info')
for item in all_screens:
    my_disp.__class__ = (
        type('%s_extended_with_%s' % (my_disp.__class__.__name__,
                                      eval(item.title()).__name__),
             (my_disp.__class__, eval(item.title())), {})
        )

# Loads data from darksky.net into class variables.
syslog.syslog('Retreiving intial weather data')
screen_info['daily']['last_update_time'] = my_disp.get_forecast(0)
screen_info['hourly']['last_update_time'] = screen_info[
    'daily']['last_update_time']
if screen_info['daily']['last_update_time'] is False:
    print('Error: no data from darksky.net.')
    running = False
syslog.syslog('Successfully retreived intial weather data.')

# Fetch initial data for other plugins
for plugin in config.PLUGINS:
    if plugin != 'daily' and plugin != 'hourly':
        syslog.syslog('Retreiving intial %s data' % plugin)
        last_update_time = eval(f"my_disp.get_{plugin}(0)")
        screen_info[plugin]['last_update_time'] = last_update_time
        if isinstance(last_update_time, int):
            syslog.syslog('Successfully retreived intial %s data' % plugin)
        else:
            syslog.syslog(
                'Error retreiving intial %s data. It will not be shown.'
                % plugin)
            del(screen_info[plugin])


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:
    # Look for and process keyboard events to change modes.
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            # On 'q' or keypad enter key, quit the program.
            if ((event.key == pygame.K_KP_ENTER) or (event.key == pygame.K_q)):
                running = False
            # On 's' key, save a screen shot.
            elif event.key == pygame.K_s:
                my_disp.screen_cap()
            else:
                # On 'd' key, set mode to 'weather mode' - daily screen.
                if event.key == pygame.K_d:
                    mode = 'daily'
                # On 'i' key, set mode to 'info'.
                elif event.key == pygame.K_i:
                    mode = 'info'
                # on 'h' key, set mode to 'weather mode' - 'hourly'
                elif event.key == pygame.K_h:
                    mode = 'hourly'
                reset_counter(mode, screen_info)
                info_screen_time_count = 0
                non_info_screen_time_count = 0

    # Automatically switch back to weather display after info screen pause.
    if mode not in screen_info.keys():
        non_info_screen_time_count = 0
        info_screen_time_count += 1
        # Default in config.py.sample: pause for 5 minutes on info screen.
        if info_screen_time_count > info_config.PAUSE:
            mode = 'daily'
            reset_counter(mode, screen_info)
            syslog.syslog(
                "Switching from INFO screen to DAILY screen at %s seconds"
                % info_screen_time_count)
    else:
        info_screen_time_count = 0
        non_info_screen_time_count += 1
        # Update / Refresh the switching time after each second.
        switch_time = time_to_switch(screen_info)

        # Default in config.py.sample: flip between 2 weather screens
        # for 15 minutes before showing info screen.
        if non_info_screen_time_count > info_config.DELAY:
            mode = 'info'
            syslog.syslog("Switching to INFO screen at %s seconds"
                          % non_info_screen_time_count)
        elif (non_info_screen_time_count % switch_time) == 0:
            new_screen = list(screen_info)[(
                list(screen_info).index(mode) + 1) % len(screen_info.keys())]
            syslog.syslog(
                "Switching from %s screen to %s screen at %s seconds" % (
                    mode.upper(), new_screen.upper(),
                    non_info_screen_time_count))
            mode = new_screen
            screen_info[mode]['count'] += 1

    try:
        if mode == 'daily' or mode == 'hourly' or mode == 'info':
            eval(f"my_disp.disp_{mode}"
                 f"(screen_info['daily']['last_update_time'])")
            last_update_time = eval(f"my_disp.get_{mode}"
                                    f"(screen_info['daily']"
                                    f"['last_update_time'])")
            screen_info['daily']['last_update_time'] = last_update_time
            screen_info['hourly']['last_update_time'] = last_update_time
        else:
            eval(f"my_disp.disp_{mode}"
                 f"(screen_info[mode]['last_update_time'])")
            last_update_time = eval(
                f"my_disp.get_{mode}(screen_info[mode]['last_update_time'])")
            screen_info[mode]['last_update_time'] = last_update_time
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        print("Decoding JSON has failed", sys.exc_info()[0])
    except BaseException:
        print("Unexpected error:", sys.exc_info()[0])

    # Loop timer.
    pygame.time.wait(1000)


pygame.quit()
