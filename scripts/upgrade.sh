if [[ -f ../config.json ]]; then
  if [[ $(grep 0.0.13 config.json) ]]; then
    echo "Configuration file type is up to date."
  else
    echo "Unknown version. Error in config.json"
else if [[ -f config.py ]]; then
  echo "Upgrading to new config format."
  if [[ ! $(grep -e 'PLUGINS' config.py) ]]; then
    api_key=$(grep DS_API_KEY config.py | cut -d" " -f 3)
    echo "$api_key"
    update_freq=$(grep DS_CHECK_INTERVAL config.py | cut -d" " -f 3)
    echo "$update_freq"
    lat=$(grep LAT config.py | cut -d" " -f 3)
    echo "$lat"
    lon=$(grep LON config.py | cut -d" " -f 3)
    echo "$lon"
    units=$(grep -m 1 UNITS config.py | cut -d" " -f 3)
    echo "$units"
    lang=$(grep LANG config.py | cut -d" " -f 3)
    echo "$lang"
    if [[ $(grep FULLSCREEN config.py | cut -d" " -f 3) == "True" ]]; then
      fullscreen="yes"
    else
      fullscreen="no"
    fi
    echo "$fullscreen"
    icon_offset=$(grep LARGE_ICON_OFFSET config.py | cut -d" " -f 3)
    echo "$icon_offset"
  else
    echo "You will need to manually update plugin configurations."
  fi
else
  if [[ -f config.json-sample ]]; then
    echo "You will need to open PiWeatherRock configuration page for initial setup."
    mv config.json-sample config.json
  else
    echo "Missing congiguration file. Please try re-donwloading from GitHub."
  fi
fi
