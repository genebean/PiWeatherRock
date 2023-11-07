# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import datetime
import pygame
import time

# local imports
from piweatherrock.intl import intl


class PluginInfo:
    """
    Displays a screen providing information about this application
    along with the time of sunrise and sunset. The time and date are
    displayed in a different place than on the daily and hourly
    screens and there is no border. This is a conscious descison to
    help prevent screen burn-in.
    """

    def __init__(self, weather_rock):
        self.config = None
        self.screen = None
        self.weather = None
        self.last_update_check = None
        self.xmax = None
        self.ymax = None
        self.time_date_small_text_height = None
        self.time_date_text_height = None
        self.time_date_y_position = None
        self.time_date_small_y_position = None
        self.sunrise_string = None
        self.sunset_string = None
        self.intl = None
        self.ui_lang = None
        
        self.get_rock_values(weather_rock)

    def get_rock_values(self, weather_rock):
        self.config = weather_rock.config
        self.screen = weather_rock.screen
        self.weather = weather_rock.weather
        self.last_update_check = weather_rock.last_update_check
        self.xmax = weather_rock.xmax
        self.ymax = weather_rock.ymax
        self.time_date_small_text_height = weather_rock.time_date_small_text_height
        self.time_date_text_height = weather_rock.time_date_text_height
        self.time_date_y_position = weather_rock.time_date_y_position
        self.time_date_small_y_position = weather_rock.time_date_small_y_position
        self.sunrise_string = weather_rock.sunrise_string
        self.sunset_string = weather_rock.sunset_string
        
        #Initialize locale resources
        self.intl = intl()
        self.ui_lang = self.config["ui_lang"]

    def disp_info(self, weather_rock):
        self.get_rock_values(weather_rock)

        (in_daylight, day_hrs, day_mins, seconds_til_daylight,
         delta_seconds_til_dark) = self.daylight(self.weather)

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

        if self.config["12hour_disp"]:
            hours_and_minutes = time.strftime("%I:%M", time.localtime())
            am_pm = time.strftime(" %p", time.localtime())
        else:
            hours_and_minutes = time.strftime("%H:%M", time.localtime())
            am_pm = "hr"

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
            self.intl.get_text(self.ui_lang,"powered_by"), small_font,
            self.xmax * 0.05, 3, text_color)

        self.string_print(
            self.intl.get_text(self.ui_lang,"sunrise", {'sunrise':self.sunrise_string}),
            small_font, self.xmax * 0.05, 4, text_color)

        self.string_print(
            self.intl.get_text(self.ui_lang,"sunset", {'sunset':self.sunset_string}),
            small_font, self.xmax * 0.05, 5, text_color)

        text = self.intl.get_text(self.ui_lang,"daylight",{'hour':day_hrs,'minute':day_mins})
        self.string_print(text, small_font, self.xmax * 0.05, 6, text_color)

        # leaving row 7 blank

        if in_daylight:
            (sunset_hour, sunset_minute) = self.stot(delta_seconds_til_dark)
            text = self.intl.get_text(self.ui_lang,"sunset_at",{'hour':sunset_hour,'minute':sunset_minute})
        else:
            (sunrise_hour, sunrise_minute) = self.stot(seconds_til_daylight)
            text = self.intl.get_text(self.ui_lang,"sunrise_at",{'hour':sunrise_hour,'minute':sunrise_minute})
        self.string_print(text, small_font, self.xmax * 0.05, 8, text_color)

        # leaving row 9 blank

        text = self.intl.get_text(self.ui_lang,"check_at")
        self.string_print(text, small_font, self.xmax * 0.05, 10, text_color)

        if self.config["12hour_disp"]:
            text = "%s" % time.strftime(
                "%I:%M:%S %p %Z on %a. %d %b %Y ",
                time.localtime(self.last_update_check))
        else:
            text = "%s" % time.strftime(
                "%H:%M:%S %Z on %a. %d %b %Y ",
                time.localtime(self.last_update_check))

        self.string_print(text, small_font, self.xmax * 0.05, 11, text_color)

        # Update the display
        pygame.display.update()

    def string_print(self, text, font, x, line_number, text_color):
        """
        Prints a line of text on the display
        """
        rendered_font = font.render(text, True, text_color)
        self.screen.blit(rendered_font, (x, self.ymax * 0.075 * line_number))

    def daylight(self, weather):
        """
        Given a weather forecast containing sunrise and sunset unix
        timestamps, return true if current local time is between sunrise
        and sunset. In other words, return true if it's daytime and the sun
        is up. Also, return the number of hours:minutes of daylight in this
        day. Lastly, return the number of seconds until daybreak and sunset.
        If it's dark, daybreak is set to the number of seconds until sunrise.
        If it daytime, sunset is set to the number of seconds until the sun
        sets.

        So, five things are returned as:
         (in_daylight,
          day_hrs,
          day_mins,
          seconds_til_daylight,
          delta_seconds_til_dark).
        """
        in_daylight = False    # Default return code.

        # Get current datetime with tz's local day and time.
        tNow = datetime.datetime.now()

        # Build a datetime variable from a unix timestamp for today's sunrise.
        tSunrise = datetime.datetime.fromtimestamp(
            weather.daily[0].sunriseTime)
        tSunset = datetime.datetime.fromtimestamp(
            weather.daily[0].sunsetTime)

        # Test if current time is between sunrise and sunset.
        if (tNow > tSunrise) and (tNow < tSunset):
            in_daylight = True        # We're in Daytime
            delta_seconds_til_dark = tSunset - tNow
            seconds_til_daylight = 0
        else:
            in_daylight = False        # We're in Nighttime
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
        dDaySec = tSunset - tSunrise           # timedelta in seconds
        (day_hrs, dayMin) = self.stot(dDaySec)  # split into hours and minutes.

        return (in_daylight, day_hrs, dayMin, seconds_til_daylight,
                delta_seconds_til_dark)

    # Helper function to which takes seconds and returns (hours, minutes).
    # ###########################################################################
    def stot(self, sec):
        mins = sec.seconds // 60
        hrs = mins // 60
        return (hrs, mins % 60)
