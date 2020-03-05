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

__version__ = "0.0.13"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################

# third party imports
from svg import Parser, Rasterizer
import pygame


# The following method (load_svg) was written by github user "zgoda".
# https://gist.github.com/zgoda/16c4bb767a085743251503471c1faeb1
# Web page archive can be found at https://web.archive.org
def load_svg(filename, scale=None, size=None, clip_from=None, fit_to=None):
    """Returns Pygame Image object from rasterized SVG
    -   If scale (float) is provided and is not None, image will be scaled.
    -   If size (w, h tuple) is provided, the image will be clipped
        to specified size.
    -   If clip_from (x, y tuple) is provided, the image will be clipped
        from specified point.
    -   If fit_to (w, h tuple) is provided, image will be scaled
        to fit in specified rect.
    """
    svg = Parser.parse_file(filename)
    tx, ty = 0, 0
    if size is None:
        w, h = svg.width, svg.height
    else:
        w, h = size
        if clip_from is not None:
            tx, ty = clip_from
    if fit_to is None:
        if scale is None:
            scale = 1
    else:
        fit_w, fit_h = fit_to
        scale_w = float(fit_w) / svg.width
        scale_h = float(fit_h) / svg.height
        scale = min([scale_h, scale_w])
    rast = Rasterizer()
    req_w = int(w * scale)
    req_h = int(h * scale)
    buff = rast.rasterize(svg, req_w, req_h, scale, tx, ty)
    image = pygame.image.frombuffer(buff, (req_w, req_h), 'RGBA')
    return image


# Method to keep track of how many times a screen has been shown.
def reset_counter(mode, screen_info):
    for screen in screen_info.keys():
        if mode == screen:
            screen_info[screen]['count'] = 1
        else:
            screen_info[screen]['count'] = 0


def time_to_switch(screen_info):
    # Calculate time to switch.
    switch_time = 0
    for screen in screen_info.keys():
        switch_time += (screen_info[screen]['count'] *
                        screen_info[screen]['pause'])
    return switch_time


# Helper function to which takes seconds and returns (hours, minutes).
# ###########################################################################
def stot(sec):
    mins = sec.seconds // 60
    hrs = mins // 60
    return (hrs, mins % 60)
