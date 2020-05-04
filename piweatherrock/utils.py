# -*- coding: utf-8 -*-
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import datetime


# Helper function to which takes seconds and returns (hours, minutes).
# ###########################################################################
def stot(sec):
    mins = sec.seconds // 60
    hrs = mins // 60
    return (hrs, mins % 60)


# Given a sunrise and sunset unix timestamp,
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the
# number of hours:minutes of daylight in this day. Lastly, return the
# number of seconds until daybreak and sunset. If it's dark, daybreak is
# set to the number of seconds until sunrise. If it daytime, sunset is set
# to the number of seconds until the sun sets.
#
# So, five things are returned as:
#  (InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def daylight(weather):
    inDaylight = False    # Default return code.

    # Get current datetime with tz's local day and time.
    tNow = datetime.datetime.now()

    # Build a datetime variable from a unix timestamp for today's sunrise.
    tSunrise = datetime.datetime.fromtimestamp(
        weather.daily[0].sunriseTime)
    tSunset = datetime.datetime.fromtimestamp(
        weather.daily[0].sunsetTime)

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
            sunrise_tomorrow = datetime.datetime.fromtimestamp(
                weather.daily[1].sunriseTime)
            seconds_til_daylight = sunrise_tomorrow - tNow
        else:
            # Else, must be early morning hours. Time to sunrise is
            # just the delta between sunrise and now.
            seconds_til_daylight = tSunrise - tNow

    # Compute the delta time (in seconds) between sunrise and set.
    dDaySec = tSunset - tSunrise           # timedelta in seconds
    (dayHrs, dayMin) = stot(dDaySec)  # split into hours and minutes.

    return (inDaylight, dayHrs, dayMin, seconds_til_daylight,
            delta_seconds_til_dark)
