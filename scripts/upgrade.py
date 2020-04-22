import json
import os
import socket

pi_ip = socket.gethostbyname(socket.gethostname() + ".local")

if os.path.exists("config.py"):
    print(f"\nImporting current configuration settings.\n\n"
          f"Go to http://{pi_ip}:8888 to view new configuration interface.\n")
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
elif os.path.exists("config.json"):
    with open("config.json", "r") as f:
        old_config = json.load(f)
else:
    with open("config.json-sample", "r") as f:
        old_config = json.load(f)
    print(f"\nYou must configure PiWeatherRock.\n\n"
          f"Go to http://{pi_ip}:8888 to configure.\n")

with open("config.json-sample", "r") as f:
    new_config = json.load(f)

# Add any new config variables
for key in new_config.keys():
    if key not in old_config.keys():
        old_config[key] = new_config[key]

with open("config.json", "w") as f:
    json.dump(old_config, f)

