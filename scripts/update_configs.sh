#!/bin/sh

if [[ $(grep -e 'PLUGINS' /home/user/Downloads/tmp/PiWeatherRock/config.py) ]]; then
  echo "No need to update config.py"
else
  echo "Updating config.py"
  cat <<EOT >> /home/user/Downloads/tmp/PiWeatherRock/config.py

# Comma separated list of plugins to display. Default behavior is to switch
# beteen daily and hourly weather. Will be shown in the order below.
PLUGINS = ['daily','hourly']
EOT
  sed '/^# Number of/d' /home/user/Downloads/tmp/PiWeatherRock/config.py > tmpfile ; mv tmpfile /home/user/Downloads/tmp/PiWeatherRock/config.py
  sed '/^DAILY/d' /home/user/Downloads/tmp/PiWeatherRock/config.py > tmpfile ; mv tmpfile /home/user/Downloads/tmp/PiWeatherRock/config.py
  sed '/^HOURLY/d' /home/user/Downloads/tmp/PiWeatherRock/config.py > tmpfile ; mv tmpfile /home/user/Downloads/tmp/PiWeatherRock/config.py
  sed '/^INFO/d' /home/user/Downloads/tmp/PiWeatherRock/config.py > tmpfile ; mv tmpfile /home/user/Downloads/tmp/PiWeatherRock/config.py
  sed '/^$/N;/^\n$/D' /home/user/Downloads/tmp/PiWeatherRock/config.py > tmpfile ; mv tmpfile /home/user/Downloads/tmp/PiWeatherRock/config.py
  echo "Updating plugin configs"
  cp '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/info_config.py.sample' '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/info_config.py'
  cp '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/daily_config.py.sample' '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/daily_config.py'
  cp '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/hourly_config.py.sample' '/home/user/Downloads/tmp/PiWeatherRock/plugin_configs/hourly_config.py'
fi
