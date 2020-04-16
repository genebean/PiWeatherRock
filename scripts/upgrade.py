import json
import os
import re
from shutil import copyfile
import socket

pi_ip = socket.gethostbyname(socket.gethostname() + ".local")

if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        old_config = json.load(f)
    with open("config.json-sample", "r") as f:
        new_config = json.load(f)
    old_major, old_minor, old_build = [int(x) for x in
                                       old_config['version'].split(".")]
    new_major, new_minor, new_build = [int(x) for x in
                                       new_config['version'].split(".")]
    if old_build > new_build:
        print(f"Error: Current version number is greater than the most "
              f"recently released version.")
    elif new_build == old_build:
        print("No upgrade needed. This is the most recently released version.")
    else:
        # Add any new config variables to config.json
        old_config["version"] = new_config["version"]
        for key in new_config.keys():
            if key not in old_config.keys():
                old_config[key] = new_config[key]
        with open("config.json", "w") as f:
            json.dump(old_config, f)
elif os.path.exists("config.py"):
    print(f"\nImporting current configuration settings.\n\n"
          f"Go to http://{pi_ip}:8888 to view new configuration interface.\n")
    old_config_dict = {}
    with open("config.py", "r") as f:
        old_config = f.read()
    old_config_dict["ds_api_key"] = re.findall(
        r"(?<=DS_API_KEY = \').*?(?=')", old_config)[0]
    old_config_dict["update_freq"] = int(re.findall(
        r"(?<=DS_CHECK_INTERVAL = )\d+", old_config)[0])
    old_config_dict["lat"] = float(re.findall(
        r"(?<=LAT = )[0-9\.-]+", old_config)[0])
    old_config_dict["lon"] = float(re.findall(
        r"(?<=LON = )[0-9\.-]+", old_config)[0])
    old_config_dict["units"] = re.findall(
        r"(?<=UNITS = \').*?(?=\')", old_config)[0]
    old_config_dict["lang"] = re.findall(
        r"(?<=LANG = \').*?(?=\')", old_config)[0]
    fs_test = re.findall(
        r"(?<=FULLSCREEN = )(?:True|False)", old_config, re.IGNORECASE)[0]
    if "t" in [ch for ch in fs_test.lower()]:
        old_config_dict["fullscreen"] = True
    else:
        old_config_dict["fullscreen"] = False
    old_config_dict["icon_offset"] = float(re.findall(
        r"(?<=LARGE_ICON_OFFSET = )[0-9.-]+", old_config)[0])

    daily_pause_list = re.findall(
        r"(?<=DAILY_PAUSE = )[0-9.-]+", old_config)
    hourly_pause_list = re.findall(
        r"(?<=HOURLY_PAUSE = )[0-9.-]+", old_config)
    info_pause_list = re.findall(
        r"(?<=INFO_SCREEN_PAUSE = )[0-9.-]+", old_config)
    info_delay_list = re.findall(
        r"(?<=INFO_SCREEN_DELAY = )[0-9.-]+", old_config)

    if (daily_pause_list and hourly_pause_list and
            info_pause_list and info_delay_list):
        old_config_dict["plugins"] = {}
        old_config_dict["plugins"]["daily"] = {}
        old_config_dict["plugins"]["hourly"] = {}
        old_config_dict["plugins"]["daily"]["pause"] = int(daily_pause_list[0])
        old_config_dict["plugins"]["daily"]["enabled"] = True
        old_config_dict["plugins"]["hourly"]["pause"] = int(hourly_pause_list[0])
        old_config_dict["plugins"]["hourly"]["enabled"] = True
        old_config_dict["info_pause"] = int(info_pause_list[0])
        old_config_dict["info_delay"] = int(info_delay_list[0])
    with open("config.json-sample", "r") as f:
        new_config_dict = json.load(f)
    for key in old_config_dict.keys():
        new_config_dict[key] = old_config_dict[key]
    with open("config.json", "w") as f:
        json.dump(new_config_dict, f)
    os.remove("config.py")
else:
    copyfile("config.json-sample", "config.json")
    print(f"\nYou must configure PiWeatherRock.\n\n"
          f"Go to http://{pi_ip}:8888 to configure.\n")
