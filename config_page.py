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

""" Configuration page for PiWeatherRock. """

__version__ = "0.0.12"


# standard imports
import os
import json
import time

# third-party imports
import cherrypy

with open(os.path.join(os.getcwd(), 'config.html'), 'r') as f:
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
        print("Config updated to:")
        print(input_json)
        with open(dst, 'w') as f:
            json.dump(input_json, f, indent=4, separators=(',', ': '))
        self.index()

    @cherrypy.expose
    def start(self):
        with open(".lock", 'w') as f:
            f.write("1")
        self.index()

    @cherrypy.expose
    def stop(self):
        with open(".lock", 'w') as f:
            f.write("0")
        self.index()

    @cherrypy.expose
    def log(self):
        with open(".log", "r") as f:
            log = f.read()
        return f"""
            <html>
                <head>
                    <title>PiWeatherRock Log</title>
                    <link rel="stylesheet" href="style.css" type="text/css" />
                </head>
                <body>
                    <a href="index">< Back to Configuration Page</a>
                    <div class="page_title">PiWeatherRock Log</div>
                    <br>
                    <div class="log">
                        <br>
                        <a href="#anchor">Jump to latest log entry</a>
                        <br>
                        <div id="scroller">
                            <!-- append content here -->
                            <pre>{log}</pre>
                            <br>
                            <button onclick="javascript:window.location.reload(true)" class="refresh">Refresh Log</button>
                            <br>
                            <br>
                            <div><a href="index">< Back to Configuration Page</a></div>
                            <div id="anchor"></div>
                        </div>
                    </div>
                </body>
            </html>"""


if __name__ == '__main__':
    cherrypy.quickstart(Config(), config={
        'global': {
            'server.socket_port': 8088,
            'server.socket_host': '0.0.0.0'
            },
        '/style.css': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "style.css")
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
        '/log': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "log")
        },
        '/.lock': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), ".lock")
        },
        '/config.json': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(
                os.getcwd(), "config.json")
        }
    })
