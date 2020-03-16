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

""" Functions to help PiWeatherRock run efficiently. """

__version__ = "0.0.12"


# third party imports
from svg import Parser, Rasterizer
import pygame
import json
import logging
import logging.handlers

def get_logger():
    with open("config.json", "r") as f:
        config = json.load(f)
    lvl_str = f"logging.{config['log_level']}"
    logging.basicConfig(
        filename='.log',
        level=eval(lvl_str),
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(
              ".log", maxBytes=500000, backupCount=3)
    log.addHandler(handler)

    return log


log = get_logger()


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
    image = pygame.image.frombuffer(buff, (req_w, req_h), "RGBA")
    return image


# Method to keep track of how many times a screen has been shown.
def reset_counter(mode, config):
    for plugin in config["plugins"].keys():
        if config["plugins"][plugin]["enabled"] == "yes":
            if plugin == mode:
                config["plugins"][plugin]["count"] = 1
            else:
                config["plugins"][plugin]["count"] = 0


def time_to_switch(config):
    # Calculate time to switch.
    switch_time = 0
    for plugin in config["plugins"].keys():
        switch_time += (int(config["plugins"][plugin]["count"]) *
                        int(config["plugins"][plugin]["pause"]))
    return switch_time


# Helper function to which takes seconds and returns (hours, minutes).
# ###########################################################################
def stot(sec):
    mins = sec.seconds // 60
    hrs = mins // 60
    return (hrs, mins % 60)


def load_config():
    log.info("Reloading most recent configuration info.")
    with open("config.json", "r") as f:
        config = json.load(f)
    for plugin in config["plugins"].keys():
        config["plugins"][plugin]["count"] = 0
        config["plugins"][plugin]["last_update_time"] = 0
    if config["plugins"]["daily"]["enabled"] == "yes":
        default = "daily"
    else:
        default = "hourly"
    return config, default
