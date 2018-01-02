# PiWeatherRock - Displays local weather on a Raspberry Pi

_Designed with a 3.5" 480x320 TFT display in mind_

## Introduction

PiWeatherRock is an internet-connected weather station. Its purpose is to
display local weather condtions. It was created with the goal of having a
simple way to check the weather before taking our dogs out for a walk. The end
result is a modern version of a weather rock.

Right now all data is pulled from Weather Underground. The next interation
will also incorporate data from sensors connected to a battery powered Arduino.

## Usage

The first thing you need to do to run this applicaiton is go to
https://www.wunderground.com/weather/api/d/docs and get an API key. After
getting a key, copy `config.py.sample` to `config.py` and fill in values for
your setup.

Once you have your config file in place, you will need to install dependancies:
via `pip install -r requirements.txt`

Now you should be able to run `python weather.py` to start the program. While
its running there are some keyboard shortcuts to see additional information:

* __w__: Displays the main weather screen
* __h__: Displays the help screen which contains some diagnostic info along
  with the current conditions
* __c__: Displays a calendar
* __q__: Quits the program 

## Influence and Credit

### Weather.py - A PyGame-based weather data/forecast display

* The buld of this project originated with the code written by Jim Kemp and
  published at
  http://www.instructables.com/id/Raspberry-Pi-Internet-Weather-Station/.
* Some ideas were also taken from
  https://github.com/sarnold/pitft-weather-display.
* Almost all the icons have been replaced with ones from
  https://github.com/manifestinteractive/weather-underground-icons. The version
  currently in use are from commit
  [47aca0a69c1246d80ee1b915c4f9906adbaa1e1b](https://github.com/manifestinteractive/weather-underground-icons/tree/47aca0a69c1246d80ee1b915c4f9906adbaa1e1b)
* Jim Kemp's version pulled from weather.com via pywapi but that doesn't seem
  seem to work any longer. This project now pulls from Weather Underground.
