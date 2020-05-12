#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

###############################################################################
#   Raspberry Pi Weather Display Config Page Plugin
#   Original By: github user: metaMMA          2020-03-15
###############################################################################

import json
import os
import socket

from argparse import ArgumentParser

pi_ip = socket.gethostbyname(socket.gethostname() + ".local")


def migrate_to_json_config(config_location):
    print(f"\nImporting current configuration settings.\n\n"
          f"Go to http://{pi_ip}:8888 to view new configuration interface.\n")

    # cd to the folder where config.py resides
    config_dir = os.path.dirname(os.path.abspath(config_location))
    os.chdir(config_dir)

    # import the old config
    import config

    old_config = {}
    old_config["ds_api_key"] = config.DS_API_KEY
    old_config["update_freq"] = int(config.DS_CHECK_INTERVAL)
    old_config["lat"] = float(config.LAT)
    old_config["lon"] = float(config.LON)
    old_config["units"] = config.UNITS
    old_config["lang"] = config.LANG
    old_config["fullscreen"] = config.FULLSCREEN
    old_config["icon_offset"] = float(config.LARGE_ICON_OFFSET)
    old_config["plugins"] = {}
    old_config["plugins"]["daily"] = {}
    old_config["plugins"]["hourly"] = {}
    old_config["plugins"]["daily"]["enabled"] = True
    old_config["plugins"]["hourly"]["enabled"] = True
    if hasattr(config, "DAILY_PAUSE"):
        old_config["plugins"]["daily"]["pause"] = int(config.DAILY_PAUSE)
    else:
        old_config["plugins"]["daily"]["pause"] = 60
    if hasattr(config, "HOURLY_PAUSE"):
        old_config["plugins"]["hourly"]["pause"] = int(config.HOURLY_PAUSE)
    else:
        old_config["plugins"]["hourly"]["pause"] = 60
    if hasattr(config, "INFO_PAUSE"):
        old_config["info_pause"] = int(config.INFO_PAUSE)
    else:
        old_config["info_pause"] = 300
    if hasattr(config, "INFO_DELAY"):
        old_config["info_delay"] = int(config.INFO_DELAY)
    else:
        old_config["info_delay"] = 900
    os.remove("config.py")

    # get out of the git repo since its not used any more
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    return old_config


def main():
    parser = ArgumentParser(
        """
        Creates or updates a configuration file.
        """)
    parser.add_argument(
        '-c', '--config', required=True,
        help='Path to your config.json file')
    parser.add_argument(
        '-o', '--oldconfig', required=False,
        help='Path to your old config.py file')
    parser.add_argument(
        '-s', '--sample', required=True,
        help="""
        Path to config.json-sample.
        This file is included automatically when installing via pip.
        You can locate it with the 'find' command like so:
        find /usr/local -type f -name config.json-sample
        """)

    args = parser.parse_args()
    config_file = os.path.abspath(args.config)
    sample_file = os.path.abspath(args.sample)

    if args.oldconfig is not None and os.path.exists(args.oldconfig):
        old_config_file = os.path.abspath(args.oldconfig)
        old_config = migrate_to_json_config(old_config_file)

    elif os.path.exists('/home/pi/config.py'):
        old_config = migrate_to_json_config('/home/pi/config.py')

    elif os.path.exists(config_file):
        with open(config_file, "r") as f:
            old_config = json.load(f)

    elif os.path.exists(sample_file):
        with open(sample_file, "r") as f:
            old_config = json.load(f)
        print(f"\nYou must configure PiWeatherRock.\n\n"
              f"Go to http://{pi_ip}:8888 to configure.\n")

    with open(sample_file, "r") as f:
        new_config = json.load(f)

    # Add any new config variables
    for key in new_config.keys():
        if key not in old_config.keys():
            old_config[key] = new_config[key]

    with open(config_file, "w") as f:
        json.dump(old_config, f)


if __name__ == '__main__':
    main()
