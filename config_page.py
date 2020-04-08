#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

""" Configuration page for PiWeatherRock. """

__version__ = "0.0.13"

###############################################################################
#   Raspberry Pi Weather Display Config Page Plugin
#   Original By: github user: metaMMA          2020-03-15
###############################################################################

# standard imports
import os
import json

# third-party imports
import cherrypy

with open(os.path.join(os.getcwd(), 'html/config.html'), 'r') as f:
    html = f.read()


class Config:

    @cherrypy.expose()
    def index(self):
        return html

    @cherrypy.tools.json_in()
    @cherrypy.expose
    def upload(self):
        dst = f"{os.getcwd()}/config.json"

        input_json = cherrypy.request.json
        with open(dst, 'w') as f:
            json.dump(input_json, f, indent=2, separators=(',', ': '))
        self.index()


if __name__ == '__main__':
    cherrypy.quickstart(Config(), config={
        'global': {
            'server.socket_port': 8888,
            'server.socket_host': '0.0.0.0'
        },
        '/serialize_script.js': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "html/serialize_script.js")
        },
        '/style.css': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "html/style.css")
        },
        '/chancetstorms.png': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "icons/256/chancetstorms.png")
        },
        '/bg.png': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "icons/bg.png")
        },
        '/config.json': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "config.json")
        }
    })
