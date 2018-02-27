#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
#Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
#Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>

#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:

#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
### END LICENSE

""" Fetches weather reports Weather Underground for display on small screens."""

__version__ = "0.0.9"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017
###############################################################################
import config
import calendar
import datetime
import json
import os
import platform
import pygame
from pygame.locals import *
import random
import requests
import serial
import string
import syslog
import time

from X10 import *

# Setup GPIO pin BCM GPIO04
if platform.machine() == 'x86_64':
    import GPIOmock as GPIO
else:
    import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # Next
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # Shutdown

mouseX, mouseY = 0, 0
mode = 'w'               # Default to weather mode.


###############################################################################

# Small LCD Display.
class SmDisplay:
    screen = None

    ####################################################################
    def __init__(self):
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

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
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
        #for fontname in pygame.font.get_fonts():
        #        print fontname
        self.temp = ''
        self.feels_like = 0
        self.wind_speed = 0
        self.baro = 0.0
        self.wind_dir = 'S'
        self.humid = 0
        self.last_update_check = ''
        self.observation_time = ''
        self.day = [ '', '', '', '' ]
        self.icon = [ 0, 0, 0, 0 ]
        self.rain = [ '', '', '', '' ]
        self.temps = [ ['',''], ['',''], ['',''], ['',''] ]
        self.sunrise = '7:00 AM'
        self.sunset = '8:00 PM'

        if config.FULLSCREEN:
          self.xmax = pygame.display.Info().current_w - 35
          self.ymax = pygame.display.Info().current_h - 5
          self.iconFolder = 'icons/256x256/'
        else:
          self.xmax = 480 - 35
          self.ymax = 320 - 5
          self.iconFolder = 'icons/64x64/'
        self.subwinTh = 0.055        # Sub window text height
        self.tmdateTh = 0.115        # Time & Date Text Height
        self.tmdateSmTh = 0.075
        self.tmdateYPos = 8          # Time & Date Y Position
        self.tmdateYPosSm = 18       # Time & Date Y Position Small



    ####################################################################
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    ####################################################################
    def UpdateWeather( self ):
        if (self.observation_time == '') or (time.time() - self.last_update_check > config.WU_CHECK_INTERVAL):
            self.last_update_check = time.time()

            # This is where the magic happens.
            url = 'http://api.wunderground.com/api/%s/alerts/astronomy/conditions/forecast/q/%s.json' % (config.WU_API_KEY, config.ZIP_CODE)
            self.weather = requests.get(url).json()
            co = self.weather['current_observation']
            sun = self.weather['sun_phase']
            moon = self.weather['moon_phase']
            sf = self.weather['forecast']['simpleforecast']['forecastday']
            tf = self.weather['forecast']['txt_forecast']['forecastday']

            try:
                if ( str(co['observation_time_rfc822']) != self.observation_time ):
                    self.observation_time = str(co['observation_time_rfc822'])
                    print "New Weather Update: " + self.observation_time
                    self.temp = str(co['temp_f'])
                    self.feels_like = str(co['feelslike_f'])
                    self.wind_speed = str(co['wind_mph'])
                    self.baro = str(co['pressure_in'])
                    self.wind_dir = str(co['wind_dir'])
                    self.humid = str(co['relative_humidity'])
                    self.vis = str(co['visibility_mi'])
                    self.gust = str(co['wind_gust_mph'])
                    self.wind_direction = str(co['wind_dir'])
                    self.day[0] = str(sf[0]['date']['weekday'])
                    self.day[1] = str(sf[1]['date']['weekday'])
                    self.day[2] = str(sf[2]['date']['weekday'])
                    self.day[3] = str(sf[3]['date']['weekday'])
                    self.sunrise = "%s:%s" % (sun['sunrise']['hour'], sun['sunrise']['minute'])
                    self.sunset = "%s:%s" % (sun['sunset']['hour'], sun['sunset']['minute'])
                    self.icon[0] = str(sf[0]['icon'])
                    self.icon[1] = str(sf[1]['icon'])
                    self.icon[2] = str(sf[2]['icon'])
                    self.icon[3] = str(sf[3]['icon'])
                    print 'WU Icons: ', self.icon[0], self.icon[1], self.icon[2], self.icon[3]
                    #print 'File: ', sd+self.icon[0]]
                    self.rain[0] = str(sf[0]['pop'])
                    self.rain[1] = str(sf[1]['pop'])
                    self.rain[2] = str(sf[2]['pop'])
                    self.rain[3] = str(sf[3]['pop'])
                    self.temps[0][0] = str(sf[0]['high']['fahrenheit']) + unichr(0x2109)
                    self.temps[0][1] = str(sf[0]['low']['fahrenheit']) + unichr(0x2109)
                    self.temps[1][0] = str(sf[1]['high']['fahrenheit']) + unichr(0x2109)
                    self.temps[1][1] = str(sf[1]['low']['fahrenheit']) + unichr(0x2109)
                    self.temps[2][0] = str(sf[2]['high']['fahrenheit']) + unichr(0x2109)
                    self.temps[2][1] = str(sf[2]['low']['fahrenheit']) + unichr(0x2109)
                    self.temps[3][0] = str(sf[3]['high']['fahrenheit']) + unichr(0x2109)
                    self.temps[3][1] = str(sf[3]['low']['fahrenheit']) + unichr(0x2109)
            except KeyError:
                print "KeyError -> Weather Error"
                self.temp = '??'
                self.observation_time = ''
                return False
            #except ValueError:
            #    print "ValueError -> Weather Error"

        return True



    ####################################################################
    def disp_weather(self):
        # Fill the screen with black
        self.screen.fill( (0,0,0) )
        xmin = 10
        xmax = self.xmax
        ymax = self.ymax
        lines = 5
        lc = (255,255,255)
        fn = "freesans"

        # Draw Screen Border
        pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )                     # Top
        pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )                  # Left
        pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )               # Bottom
        pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax+2), lines )                # Right
        pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )     # Bottom of top box
        pygame.draw.line( self.screen, lc, (xmin,ymax*0.5),(xmax,ymax*0.5), lines )       # Bottom of middle box
        pygame.draw.line( self.screen, lc, (xmax*0.25,ymax*0.5),(xmax*0.25,ymax), lines ) # Bottom row, left vertical
        pygame.draw.line( self.screen, lc, (xmax*0.5,ymax*0.15),(xmax*0.5,ymax), lines )  # Bottom row, center vertical
        pygame.draw.line( self.screen, lc, (xmax*0.75,ymax*0.5),(xmax*0.75,ymax), lines ) # Bottom row, right vertical

        # Time & Date
        th = self.tmdateTh
        sh = self.tmdateSmTh
        font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )        # Regular Font
        sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 )       # Small Font for Seconds

        tm1 = time.strftime( "%a, %b %d   %I:%M", time.localtime() )  # time
        tm2 = time.strftime( " %P", time.localtime() )                # am/pm

        rtm1 = font.render( tm1, True, lc )
        (tx1,ty1) = rtm1.get_size()
        rtm2 = sfont.render( tm2, True, lc )
        (tx2,ty2) = rtm2.get_size()

        tp = xmax / 2 - (tx1 + tx2) / 2
        self.screen.blit( rtm1, (tp,self.tmdateYPos) )
        self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )

        # Outside Temp
        font = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.6), bold=1 )
        txt = font.render( self.temp, True, lc )
        (tx,ty) = txt.get_size()
        # Show degree F symbol using magic unicode char in a smaller font size.
        dfont = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.3), bold=1 )
        dtxt = dfont.render( unichr(0x2109), True, lc )
        (tx2,ty2) = dtxt.get_size()
        x = xmax*0.27 - (tx*1.02 + tx2) / 2
        self.screen.blit( txt, (x,ymax*0.20) )
        #self.screen.blit( txt, (xmax*0.02,ymax*0.15) )
        x = x + (tx*1.02)
        self.screen.blit( dtxt, (x,ymax*0.2) )
        #self.screen.blit( dtxt, (xmax*0.02+tx*1.02,ymax*0.2) )

        # Conditions
        st = 0.17    # Yaxis Start Pos
        gp = 0.065   # Line Spacing Gap
        th = 0.05    # Text Height
        dh = 0.03    # Degree Symbol Height
        so = 0.001   # Degree Symbol Yaxis Offset
        xp = 0.52    # Xaxis Start Pos
        x2 = 0.73    # Second Column Xaxis Start Pos

        font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
        txt = font.render( 'Feels Like:', True, lc )
        self.screen.blit( txt, (xmax*xp,ymax*st) )
        txt = font.render( self.feels_like, True, lc )
        self.screen.blit( txt, (xmax*x2,ymax*st) )
        (tx,ty) = txt.get_size()
        # Show degree F symbol using magic unicode char.
        dfont = pygame.font.SysFont( fn, int(ymax*dh), bold=1 )
        dtxt = dfont.render( unichr(0x2109), True, lc )
        self.screen.blit( dtxt, (xmax*x2+tx*1.01,ymax*(st+so)) )

        txt = font.render( 'Currently:', True, lc )
        self.screen.blit( txt, (xmax*xp,ymax*(st+gp*1)) )
        txt = font.render( self.weather['current_observation']['weather'], True, lc )
        self.screen.blit( txt, (xmax*x2,ymax*(st+gp*1)) )

        txt = font.render( 'Windspeed:', True, lc )
        self.screen.blit( txt, (xmax*xp,ymax*(st+gp*2)) )
        txt = font.render( self.wind_speed+' mph', True, lc )
        self.screen.blit( txt, (xmax*x2,ymax*(st+gp*2)) )

        txt = font.render( 'Direction:', True, lc )
        self.screen.blit( txt, (xmax*xp,ymax*(st+gp*3)) )
        txt = font.render( string.upper(self.wind_dir), True, lc )
        self.screen.blit( txt, (xmax*x2,ymax*(st+gp*3)) )

        txt = font.render( 'Humidity:', True, lc )
        self.screen.blit( txt, (xmax*xp,ymax*(st+gp*4)) )
        txt = font.render( self.humid, True, lc )
        self.screen.blit( txt, (xmax*x2,ymax*(st+gp*4)) )

        wx =     0.125            # Sub Window Centers
        wy =     0.530            # Sub Windows Yaxis Start
        th =     self.subwinTh    # Text Height
        rpth =   0.060            # Rain Present Text Height
        gp =     0.065            # Line Spacing Gap
        ro =     0.010 * xmax     # "Rain:" Text Window Offset winthin window.
        rpl =    5.95             # Rain percent line offset.

        font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
        rpfont = pygame.font.SysFont( fn, int(ymax*rpth), bold=1 )

        # Sub Window 1
        txt = font.render( 'Today:', True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*wx-tx/2,ymax*(wy+gp*0)) )
        txt = font.render( self.temps[0][0] + ' / ' + self.temps[0][1], True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*wx-tx/2,ymax*(wy+gp*5)) )
        #rtxt = font.render( 'Rain:', True, lc )
        #self.screen.blit( rtxt, (ro,ymax*(wy+gp*5)) )
        rptxt = rpfont.render( self.rain[0]+'%', True, lc )
        (tx,ty) = rptxt.get_size()
        self.screen.blit( rptxt, (xmax*wx-tx/2,ymax*(wy+gp*rpl)) )
        icon = pygame.image.load(self.iconFolder + self.icon[0] + '.png').convert_alpha()
        (ix,iy) = icon.get_size()
        if ( iy < 90 ):
            yo = (90 - iy) / 2
        else:
            yo = 0
        self.screen.blit( icon, (xmax*wx-ix/2,ymax*(wy+gp*1.2)+yo) )

        # Sub Window 2
        txt = font.render( self.day[1]+':', True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*(wx*3)-tx/2,ymax*(wy+gp*0)) )
        txt = font.render( self.temps[1][0] + ' / ' + self.temps[1][1], True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*wx*3-tx/2,ymax*(wy+gp*5)) )
        #self.screen.blit( rtxt, (xmax*wx*2+ro,ymax*(wy+gp*5)) )
        rptxt = rpfont.render( self.rain[1]+'%', True, lc )
        (tx,ty) = rptxt.get_size()
        self.screen.blit( rptxt, (xmax*wx*3-tx/2,ymax*(wy+gp*rpl)) )
        icon = pygame.image.load(self.iconFolder + self.icon[1] + '.png').convert_alpha()
        (ix,iy) = icon.get_size()
        if ( iy < 90 ):
            yo = (90 - iy) / 2
        else:
            yo = 0
        self.screen.blit( icon, (xmax*wx*3-ix/2,ymax*(wy+gp*1.2)+yo) )

        # Sub Window 3
        txt = font.render( self.day[2]+':', True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*(wx*5)-tx/2,ymax*(wy+gp*0)) )
        txt = font.render( self.temps[2][0] + ' / ' + self.temps[2][1], True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*wx*5-tx/2,ymax*(wy+gp*5)) )
        #self.screen.blit( rtxt, (xmax*wx*4+ro,ymax*(wy+gp*5)) )
        rptxt = rpfont.render( self.rain[2]+'%', True, lc )
        (tx,ty) = rptxt.get_size()
        self.screen.blit( rptxt, (xmax*wx*5-tx/2,ymax*(wy+gp*rpl)) )
        icon = pygame.image.load(self.iconFolder + self.icon[2] + '.png').convert_alpha()
        (ix,iy) = icon.get_size()
        if ( iy < 90 ):
            yo = (90 - iy) / 2
        else:
            yo = 0
        self.screen.blit( icon, (xmax*wx*5-ix/2,ymax*(wy+gp*1.2)+yo) )

        # Sub Window 4
        txt = font.render( self.day[3]+':', True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*(wx*7)-tx/2,ymax*(wy+gp*0)) )
        txt = font.render( self.temps[3][0] + ' / ' + self.temps[3][1], True, lc )
        (tx,ty) = txt.get_size()
        self.screen.blit( txt, (xmax*wx*7-tx/2,ymax*(wy+gp*5)) )
        #self.screen.blit( rtxt, (xmax*wx*6+ro,ymax*(wy+gp*5)) )
        rptxt = rpfont.render( self.rain[3]+'%', True, lc )
        (tx,ty) = rptxt.get_size()
        self.screen.blit( rptxt, (xmax*wx*7-tx/2,ymax*(wy+gp*rpl)) )
        icon = pygame.image.load(self.iconFolder + self.icon[3] + '.png').convert_alpha()
        (ix,iy) = icon.get_size()
        if ( iy < 90 ):
            yo = (90 - iy) / 2
        else:
            yo = 0
        self.screen.blit( icon, (xmax*wx*7-ix/2,ymax*(wy+gp*1.2)+yo) )

        # Update the display
        pygame.display.update()

    ####################################################################
    def disp_calendar(self):
        # Fill the screen with black
        self.screen.fill( (0,0,0) )
        xmin = 10
        xmax = self.xmax
        ymax = self.ymax
        lines = 5
        lc = (255,255,255)
        sfn = "freemono"
        fn = "freesans"

        # Draw Screen Border
        pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
        pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )

        # Time & Date
        th = self.tmdateTh
        sh = self.tmdateSmTh
        font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )          # Regular Font
        sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 )         # Small Font for Seconds

        tm1 = time.strftime( "%a, %b %d   %I:%M", time.localtime() )    # 1st part
        tm2 = time.strftime( "%S", time.localtime() )                   # 2nd
        tm3 = time.strftime( " %P", time.localtime() )                  #

        rtm1 = font.render( tm1, True, lc )
        (tx1,ty1) = rtm1.get_size()
        rtm2 = sfont.render( tm2, True, lc )
        (tx2,ty2) = rtm2.get_size()
        rtm3 = font.render( tm3, True, lc )
        (tx3,ty3) = rtm3.get_size()

        tp = xmax / 2 - (tx1 + tx2 + tx3) / 2
        self.screen.blit( rtm1, (tp,self.tmdateYPos) )
        self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
        self.screen.blit( rtm3, (tp+tx1+tx2,self.tmdateYPos) )

        # Conditions
        ys = 0.20        # Yaxis Start Pos
        xs = 0.20        # Xaxis Start Pos
        gp = 0.075       # Line Spacing Gap
        th = 0.05        # Text Height

        #cal = calendar.TextCalendar()
        yr = int( time.strftime( "%Y", time.localtime() ) )    # Get Year
        mn = int( time.strftime( "%m", time.localtime() ) )    # Get Month
        cal = calendar.month( yr, mn ).splitlines()
        i = 0
        for cal_line in cal:
            txt = sfont.render( cal_line, True, lc )
            self.screen.blit( txt, (xmax*xs,ymax*(ys+gp*i)) )
            i = i + 1

        # Update the display
        pygame.display.update()

    ####################################################################
    def sPrint( self, s, font, x, l, lc ):
        f = font.render( s, True, lc )
        self.screen.blit( f, (x,self.ymax*0.075*l) )

    ####################################################################
    def disp_help( self, inDaylight, dayHrs, dayMins, tDaylight, tDarkness ):
        # Fill the screen with black
        self.screen.fill( (166,166,166) )
        xmax = self.xmax
        ymax = self.ymax
        xmin = 10
        lines = 5
        line_color = (166,166,166)
        text_color = (255,255,255)
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line( self.screen, line_color, (xmin,0),(xmax,0), lines )
        pygame.draw.line( self.screen, line_color, (xmin,0),(xmin,ymax), lines )
        pygame.draw.line( self.screen, line_color, (xmin,ymax),(xmax,ymax), lines )
        pygame.draw.line( self.screen, line_color, (xmax,0),(xmax,ymax), lines )
        pygame.draw.line( self.screen, line_color, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )

        time_height_large = self.tmdateTh
        time_height_small = self.tmdateSmTh

        # Time & Date
        regular_font = pygame.font.SysFont( font_name, int(ymax*time_height_large), bold=1 )
        small_font = pygame.font.SysFont( font_name, int(ymax*time_height_small), bold=1 )

        hours_and_minites = time.strftime( "%I:%M", time.localtime() )
        am_pm = time.strftime( " %P", time.localtime() )

        rendered_hours_and_minutes = regular_font.render( hours_and_minites, True, text_color )
        (tx1,ty1) = rendered_hours_and_minutes.get_size()
        rendered_am_pm = small_font.render( am_pm, True, text_color )
        (tx2,ty2) = rendered_am_pm.get_size()

        tp = xmax / 2 - (tx1 + tx2) / 2
        self.screen.blit( rendered_hours_and_minutes, (tp,self.tmdateYPos) )
        self.screen.blit( rendered_am_pm, (tp+tx1+3,self.tmdateYPosSm) )

        self.sPrint( "Sunrise: %s" % self.sunrise, small_font, xmax*0.05, 3, text_color )
        self.sPrint( "Sunset: %s" % self.sunset, small_font, xmax*0.05, 4, text_color )

        text = "Daylight (Hrs:Min): %d:%02d" % (dayHrs, dayMins)
        self.sPrint( text, small_font, xmax*0.05, 5, text_color )

        if inDaylight: text = "Sunset in (Hrs:Min): %d:%02d" % stot( tDarkness )
        else:          text = "Sunrise in (Hrs:Min): %d:%02d" % stot( tDaylight )
        self.sPrint( text, small_font, xmax*0.05, 6, text_color )

        text = ""
        self.sPrint( text, small_font, xmax*0.05, 7, text_color )

        text = "Weather checked at"
        self.sPrint( text, small_font, xmax*0.05, 8, text_color )

        text = "    %s" % time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(self.last_update_check))
        self.sPrint( text, small_font, xmax*0.05, 9, text_color )

        text = "Weather observation time:"
        self.sPrint( text, small_font, xmax*0.05, 10, text_color )

        text = "    %s" % self.observation_time
        self.sPrint( text, small_font, xmax*0.05, 11, text_color )

        # Update the display
        pygame.display.update()



    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap( self ):
        pygame.image.save( self.screen, "screenshot.jpeg" )
        print "Screen capture complete."


# Helper function to which takes seconds and returns (hours, minutes).
############################################################################
def stot( sec ):
    min = sec.seconds // 60
    hrs = min // 60
    return ( hrs, min % 60 )


# Given a sunrise and sunset time string (sunrise example format '7:00 AM'),
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the
# number of seconds until sunrise. If it daytime, sunset is set to the number
# of seconds until the sun sets.
#
# So, five things are returned as:
#  ( InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def Daylight( sr, st ):
    inDaylight = False    # Default return code.

    # Get current datetime with tz's local day and time.
    tNow = datetime.datetime.now()

    # From a string like '7:00', build a datetime variable for
    # today with the hour and minute set to sunrise.
    t = time.strptime( sr, '%H:%M' )        # Temp Var
    tSunrise = tNow                    # Copy time now.
    # Overwrite hour and minute with sunrise hour and minute.
    tSunrise = tSunrise.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )

    # From a string like '19:00', build a datetime variable for
    # today with the hour and minute set to sunset.
    t = time.strptime( myDisp.sunset, '%H:%M' )
    tSunset = tNow                    # Copy time now.
    # Overwrite hour and minute with sunset hour and minute.
    tSunset = tSunset.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )

    # Test if current time is between sunrise and sunset.
    if (tNow > tSunrise) and (tNow < tSunset):
        inDaylight = True        # We're in Daytime
        tDarkness = tSunset - tNow    # Delta seconds until dark.
        tDaylight = 0            # Seconds until daylight
    else:
        inDaylight = False        # We're in Nighttime
        tDarkness = 0            # Seconds until dark.
        # Delta seconds until daybreak.
        if tNow > tSunset:
            # Must be evening - compute sunrise as time left today
            # plus time from midnight tomorrow.
            tMidnight = tNow.replace( hour=23, minute=59, second=59 )
            tNext = tNow.replace( hour=0, minute=0, second=0 )
            tDaylight = (tMidnight - tNow) + (tSunrise - tNext)
        else:
            # Else, must be early morning hours. Time to sunrise is
            # just the delta between sunrise and now.
            tDaylight = tSunrise - tNow

    # Compute the delta time (in seconds) between sunrise and set.
    dDaySec = tSunset - tSunrise        # timedelta in seconds
    (dayHrs, dayMin) = stot( dDaySec )    # split into hours and minutes.

    return ( inDaylight, dayHrs, dayMin, tDaylight, tDarkness )


############################################################################
def btnNext( channel ):
    global mode, non_weather_timeout, periodic_help_activation

    if ( mode == 'c' ): mode = 'w'
    elif (mode == 'w' ): mode ='h'
    elif (mode == 'h' ): mode ='c'

    non_weather_timeout = 0
    periodic_help_activation = 0

    print "Button Event!"


#==============================================================
#==============================================================

try:
    ser = serial.Serial( "/dev/ttyUSB0", 4800, timeout=2 )
    serActive = True
except:
    serActive = False
    print "Warning: can't open ttyUSB0 serial port."

if serActive:
    X10 = False        # Assume no X10 until proven wrong.
    ser.flushInput()    # Dump any junk that may be there.
    ser.flushOutput()

    ser.write( chr(0x8b) )    # Querry Status
    c = ser.read( 1 )    # Wait for something from the CM11A.

    # If an attached CM11A sends a 0xA5 then it requirs a clock reset.
    if (len(c) == 1):
        if (ord(c) == 0xA5):
            X10_SetClock( ser )
    else:
        time.sleep( 0.5 )

    # Get the current status from the CM11A X10 module.
    (X10, c) = X10_Status( ser )

    if X10 == False: print 'Error: CM11A.'

    # If CM11A is present, turn on the lamp A3!
    if X10 == True:
        if X10_On( ser, housecode['A'], unitcode['3'] ):
            print 'X10 On comand OK.'
        else:
            print 'Error in X10 On command.'
        time.sleep( 2 )
        if X10_Bright( ser, housecode['A'], unitcode['3'] ):
            print 'X10 Full Bright OK.'
        else:
            print 'Error in X10 Bright command.'

#exit()


# Display all the available fonts.
#print "Fonts: ", pygame.font.get_fonts()

mode = 'w'        # Default to weather mode.

# Create an instance of the lcd display class.
myDisp = SmDisplay()

running = True             # Stay running while True
seconds = 0                # Seconds Placeholder to pace display.
non_weather_timeout = 0    # Display timeout to automatically switch back to weather dispaly.
periodic_help_activation = 0  # Switch to help periodically to prevent screen burn

# Loads data from Weather.com into class variables.
if myDisp.UpdateWeather() == False:
    print 'Error: no data from Weather.com.'
    running = False

# Attach GPIO callback to our new button input on pin #4.
GPIO.add_event_detect( 4, GPIO.RISING, callback=btnNext, bouncetime=400)
#GPIO.add_event_detect( 17, GPIO.RISING, callback=btnShutdown, bouncetime=100)
btnShutdownCnt = 0

if GPIO.input( 17 ):
    print "Warning: Shutdown Switch is Active!"
    myDisp.screen.fill( (0,0,0) )
    icon = pygame.image.load('icons/64x64/' + 'shutdown.jpg')
    (ix,iy) = icon.get_size()
    myDisp.screen.blit( icon, (800/2-ix/2,400/2-iy/2) )
    font = pygame.font.SysFont( "freesans", 40, bold=1 )
    rf = font.render( "Please toggle shutdown siwtch.", True, (255,255,255) )
    (tx1,ty1) = rf.get_size()
    myDisp.screen.blit( rf, (800/2-tx1/2,iy+20) )
    pygame.display.update()
    pygame.time.wait( 1000 )
    while GPIO.input( 17 ): pygame.time.wait(100)



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:

    # Debounce the shutdown switch. The main loop rnus at 100ms. So, if the
    # button (well, a switch really) counter "btnShutdownCnt" counts above
    # 25 then the switch must have been on continuously for 2.5 seconds.
    if GPIO.input( 17 ):
        btnShutdownCnt += 1
        if btnShutdownCnt > 25:
            print "Shutdown!"
            myDisp.screen.fill( (0,0,0) )
            icon = pygame.image.load('icons/64x64/' + 'shutdown.jpg')
            (ix,iy) = icon.get_size()
            myDisp.screen.blit( icon, (800/2-ix/2,400/2-iy/2) )
            font = pygame.font.SysFont( "freesans", 60, bold=1 )
            rtm1 = font.render( "Shuting Down!", True, (255,255,255) )
            (tx1,ty1) = rtm1.get_size()
            myDisp.screen.blit( rtm1, (800/2-tx1/2,iy+20) )
            pygame.display.update()
            pygame.time.wait( 1000 )
            #os.system("sudo shutdown -h now")
            while GPIO.input( 17 ): pygame.time.wait(100)
    else:
        btnShutdownCnt = 0

    # Look for and process keyboard events to change modes.
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            # On 'q' or keypad enter key, quit the program.
            if (( event.key == K_KP_ENTER ) or (event.key == K_q)):
                running = False

            # On 'c' key, set mode to 'calendar'.
            elif ( event.key == K_c ):
                mode = 'c'
                non_weather_timeout = 0
                periodic_help_activation = 0

            # On 'w' key, set mode to 'weather'.
            elif ( event.key == K_w ):
                mode = 'w'
                non_weather_timeout = 0
                periodic_help_activation = 0

            # On 's' key, save a screen shot.
            elif ( event.key == K_s ):
                myDisp.screen_cap()

            # On 'h' key, set mode to 'help'.
            elif ( event.key == K_h ):
                mode = 'h'
                non_weather_timeout = 0
                periodic_help_activation = 0

    # Automatically switch back to weather display after a couple minutes.
    if mode != 'w':
        periodic_help_activation = 0
        non_weather_timeout += 1
        if non_weather_timeout > 3000:    # Five minute timeout at 100ms loop rate.
            mode = 'w'
    else:
        non_weather_timeout = 0
        periodic_help_activation += 1
        if periodic_help_activation > 9000:  # 15 minute timeout at 100ms loop rate
            mode = 'h'

    # Calendar Display Mode
    if ( mode == 'c' ):
        # Update / Refresh the display after each second.
        if ( seconds != time.localtime().tm_sec ):
            seconds = time.localtime().tm_sec
            myDisp.disp_calendar()

    # Weather Display Mode
    if ( mode == 'w' ):
        # Update / Refresh the display after each second.
        if ( seconds != time.localtime().tm_sec ):
            seconds = time.localtime().tm_sec
            myDisp.disp_weather()
            #ser.write( "Weather\r\n" )
        # Once the screen is updated, we have a full second to get the weather.
        # Once per minute, update the weather from the net.
        if ( seconds == 0 ):
            try:
                myDisp.UpdateWeather()
            except ValueError: # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except:
                print("Unexpected error:", sys.exc_info()[0])

    if ( mode == 'h'):
        # Pace the screen updates to once per second.
        if seconds != time.localtime().tm_sec:
            seconds = time.localtime().tm_sec

            ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

            #if inDaylight:
            #    print "Time until dark (Hr:Min) -> %d:%d" % stot( tDarkness )
            #else:
            #    #print 'tDaylight ->', tDaylight
            #    print "Time until daybreak (Hr:Min) -> %d:%d" % stot( tDaylight )

            # Stat Screen Display.
            myDisp.disp_help( inDaylight, dayHrs, dayMins, tDaylight, tDarkness )
        # Refresh the weather data once per minute.
        if ( int(seconds) == 0 ):
            try:
                myDisp.UpdateWeather()
            except ValueError: # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except:
                print("Unexpected error:", sys.exc_info()[0])

    ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

    if serActive:
        h = housecode['A']
        u = unitcode['3']

        if time.localtime().tm_sec == 30:
            if ( inDaylight == False ):
                X10_On( ser, h, u )
                print "X10 On"
            else:
                X10_Off( ser, h, u )
                print "X10 Off"
        if time.localtime().tm_sec == 40:
            if ( inDaylight == False ):
                X10_Bright( ser, housecode['A'], unitcode['3'] )

    # Loop timer.
    pygame.time.wait( 100 )


pygame.quit()
