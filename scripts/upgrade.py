import json
import os
import re
from shutil import copyfile

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
         # This is for future upgrades.
         # Code will run when current version of config.json is older than the
         # most recently released version.
        pass
elif os.path.exists("config.py"):
    print(f"\nImporting current configuration settings.\n\n"
          f"Go to http://0.0.0.0:8888 to view new configuration interface.\n"
          f"Replace 0.0.0.0 with the IP address of the Pi, "
          f"if not running this upgrade locally\n")
    old_config_dict = {}
    with open("config.py", "r") as f:
        old_config = f.read()
    old_config_dict["api_key"] = re.findall(
        r"(?<=DS_API_KEY = \').*?(?=')", old_config)[0]
    old_config_dict["update_freq"] = re.findall(
        r"(?<=DS_CHECK_INTERVAL = )\d+", old_config)[0]
    old_config_dict["lat"] = re.findall(
        r"(?<=LAT = )[0-9\.-]+", old_config)[0]
    old_config_dict["lon"] = re.findall(
        r"(?<=LON = )[0-9\.-]+", old_config)[0]
    old_config_dict["units"] = re.findall(
        r"(?<=UNITS = \').*?(?=\')", old_config)[0]
    old_config_dict["lang"] = re.findall(
        r"(?<=LANG = \').*?(?=\')", old_config)[0]
    old_config_dict["fullscreen"] = re.findall(
        r"(?<=FULLSCREEN = )(?:True|False)", old_config)[0]
    old_config_dict["icon_offset"] = re.findall(
        r"(?<=LARGE_ICON_OFFSET = )[0-9.-]+", old_config)[0]

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
        old_config_dict["plugins"]["daily"]["pause"] = daily_pause_list[0]
        old_config_dict["plugins"]["daily"]["enabled"] = "yes"
        old_config_dict["plugins"]["hourly"]["pause"] = hourly_pause_list[0]
        old_config_dict["plugins"]["hourly"]["enabled"] = "yes"
        old_config_dict["info_pause"] = info_pause_list[0]
        old_config_dict["info_delay"] = info_delay_list[0]
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
          f"Go to http://0.0.0.0:8888 to configure.\n"
          f"Replace 0.0.0.0 with the IP address of the Pi, "
          f"if not running this upgrade locally.\n")
