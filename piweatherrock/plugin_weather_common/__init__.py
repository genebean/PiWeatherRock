# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import pygame
import time
import json

from os import path
from datetime import datetime

# local imports
from piweatherrock.intl import intl


UNICODE_DEGREE = u'\xb0'

class PluginWeatherCommon:
    """
    This plugin is resposible for displaying the information on the top
    half of the screen when either the daily or hourly forecast is being
    displayed on the lower half. Both 'plugin_weather_daily' and
    'plugin_weather_hourly' call display_weather_top() to do this.

    This plugin also provides the display_subwindow() function that is used
    by 'plugin_weather_daily' and 'plugin_weather_hourly'.
    """

    def __init__(self, weather_rock):
        self.screen = None
        self.weather = None
        self.config = None
        self.take_umbrella = None
        self.xmax = None
        self.ymax = None
        self.time_date_small_text_height = None
        self.time_date_text_height = None
        self.time_date_y_position = None
        self.time_date_small_y_position = None
        self.subwindow_text_height = None
        self.icon_size = None
        self.intl = None
        self.ui_lang = None
       
        self.get_rock_values(weather_rock)
    
    def get_rock_values(self, weather_rock):
        self.screen = weather_rock.screen
        self.weather = weather_rock.weather
        self.config = weather_rock.config
        self.take_umbrella = self.umbrella_needed()
        self.xmax = weather_rock.xmax
        self.ymax = weather_rock.ymax
        self.time_date_small_text_height = weather_rock.time_date_small_text_height
        self.time_date_text_height = weather_rock.time_date_text_height
        self.time_date_y_position = weather_rock.time_date_y_position
        self.time_date_small_y_position = weather_rock.time_date_small_y_position
        self.subwindow_text_height = weather_rock.subwindow_text_height
        self.icon_size = weather_rock.icon_size
        
        #Initialize locale resources
        self.intl = intl()
        self.ui_lang = self.config["ui_lang"]

    def disp_weather_top(self, weather_rock):
        self.get_rock_values(weather_rock)

        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        font_name = "freesans"

        self.draw_screen_border(line_color, xmin, lines)
        self.disp_time_date(font_name, text_color)
        self.disp_current_temp(font_name, text_color)
        self.disp_summary()
        self.display_conditions_line(
            self.intl.get_text(self.ui_lang,"feels_like"), int(round(self.weather.apparentTemperature)),
            True)

        try:
            wind_bearing = self.weather.windBearing
            wind_direction = self.deg_to_compass(wind_bearing) + ' @ '
        except AttributeError:
            wind_direction = ''
        wind_txt = wind_direction + str(
            int(round(self.weather.windSpeed))) + \
            ' ' + self.get_windspeed_abbreviation(self.config["units"])
        self.display_conditions_line(
            self.intl.get_text(self.ui_lang,"wind"), wind_txt, False, 1)

        self.display_conditions_line(
            self.intl.get_text(self.ui_lang,"humidity"), str(int(round((self.weather.humidity * 100)))) + '%',
            False, 2)

        # Skipping multiplier 3 (line 4)

        if self.take_umbrella:
            umbrella_txt = self.intl.get_text(self.ui_lang,"umbrella")
        else:
            umbrella_txt = self.intl.get_text(self.ui_lang,"no_umbrella")
        self.disp_umbrella_info(umbrella_txt)

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

    def disp_time_date(self, font_name, text_color):
        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)
        # Small Font for Seconds
        small_font = pygame.font.SysFont(
            font_name,
            int(self.ymax * self.time_date_small_text_height), bold=1)

        if self.config["12hour_disp"]:
            time_string = self.intl.get_datetime(self.ui_lang, datetime.utcnow(), True)
            am_pm_string = self.intl.get_ampm(self.ui_lang, datetime.utcnow())
        else:
            time_string = self.intl.get_datetime(self.ui_lang, datetime.utcnow(), False)
            am_pm_string = "hr"

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

    def disp_current_temp(self, font_name, text_color):
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
            self.get_temperature_letter(self.config["units"]),
            True, text_color)
        (degree_letter_x, degree_letter_y) = degree_letter.get_size()
        # Position text
        x = self.xmax * 0.27 - (txt_x * 1.02 + rendered_am_pm_x +
                                degree_letter_x) / 2
        self.screen.blit(txt, (x, self.ymax * 0.20))
        x = x + (txt_x * 1.02)
        self.screen.blit(degree_txt, (x, self.ymax * 0.2))
        x = x + (rendered_am_pm_x * 1.02)
        self.screen.blit(degree_letter, (x, self.ymax * 0.2))

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

    def display_conditions_line(self, label, cond, is_temp, multiplier=None):
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
                self.get_temperature_letter(self.config["units"]),
                True, text_color)
            degree_letter_x = degree_letter.get_size()[0]
            self.screen.blit(degree_letter, (
                self.xmax * second_column_x_start_position +
                txt_x + degree_letter_x * 1.01,
                self.ymax * (y_start + degree_symbol_y_offset)))

    def deg_to_compass(self, degrees):
        """
        Convert numerical direction into the letters you'd see on a compas
        such as 'N' for north or 'SE' for south east.
        """
        val = int((degrees/22.5)+.5)
        dirs = ["N", "NNE", "NE", "ENE",
                "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW",
                "W", "WNW", "NW", "NNW"]
        return dirs[(val % 16)]

    def get_windspeed_abbreviation(self, unit):
        """
        Determines the abbreviation to use for wind speed based on the unit
        a user has chosen (ca, uk2, us, si).
        """
        return self.get_abbreviation(self.units_decoder(unit)['windSpeed'])

    def umbrella_needed(self):
        # start with saying we don't need an umbrella
        take_umbrella = False
        icon_now = self.weather.icon
        icon_today = self.weather.daily[0].icon
        if icon_now == 'rain' or icon_today == 'rain':
            take_umbrella = True
        else:
            # determine if an umbrella is needed during daylight hours
            curr_date = datetime.today().date()
            for hour in self.weather.hourly:
                hr = datetime.fromtimestamp(hour.time)
                sr = datetime.fromtimestamp(
                    self.weather.daily[0].sunriseTime)
                ss = datetime.fromtimestamp(
                    self.weather.daily[0].sunsetTime)
                rain_chance = hour.precipProbability
                is_today = hr.date() == curr_date
                is_daylight_hr = hr >= sr and hr <= ss
                if is_today and is_daylight_hr and rain_chance >= .25:
                    take_umbrella = True
                    break

        return take_umbrella

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
            self.ymax*y_start_position))

    def get_temperature_letter(self, unit):
        """
        Determines the single letter that represents temperature based on
        unit a user has chosen. ex: 'F' to represent 'Degrees Fahrenheit'
        """
        return self.units_decoder(unit)['temperature'].split(' ')[-1][0].upper()

    def get_abbreviation(self, phrase):
        """
        Create an abbreviation from a phrase by combining the first letter
        of each word in lower case.
        """
        abbreviation = ''.join(item[0].lower() for item in phrase.split())
        return abbreviation

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

    #######################################################################
    #    Everything above here is used exclusively by disp_weather_top    #
    #######################################################################

    def display_subwindow(self, data, day, c_times):
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
                str(int(round(data.temperatureLow))) +
                UNICODE_DEGREE +
                ' / ' +
                str(int(round(data.temperatureHigh))) +
                UNICODE_DEGREE + self.get_temperature_letter(
                    self.config["units"]),
                True, text_color)
        else:
            txt = forecast_font.render(
                str(int(round(data.temperature))) +
                UNICODE_DEGREE + self.get_temperature_letter(
                    self.config["units"]),
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
            self.icon_mapping(data.icon, self.icon_size)).convert_alpha()
        (icon_size_x, icon_size_y) = icon.get_size()
        if icon_size_y < 90:
            icon_y_offset = (90 - icon_size_y) / 2
        else:
            icon_y_offset = self.config["icon_offset"]

        self.screen.blit(icon, (self.xmax *
                                (subwindow_centers * c_times) -
                                icon_size_x / 2,
                                self.ymax *
                                (subwindows_y_start_position +
                                 line_spacing_gap
                                 * 1.2) + icon_y_offset))

    def icon_mapping(self, icon, size):
        """
        https://darksky.net/dev/docs has this to say about icons:
        icon optional
        A machine-readable text summary of this data point, suitable for
        selecting an icon for display. If defined, this property will have one
        of the following values: clear-day, clear-night, rain, snow, sleet,
        wind, fog, cloudy, partly-cloudy-day, or partly-cloudy-night.
        (Developers should ensure that a sensible default is defined, as
        additional values, such as hail, thunderstorm, or tornado, may be
        defined in the future.)

        Based on that, this method will map the Dark Sky icon name to the name
        of an icon in this project.
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

        return path.join(path.dirname(__file__), icon_path)
