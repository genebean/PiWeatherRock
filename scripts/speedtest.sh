#!/bin/bash

/home/pi/.local/bin/speedtest-cli --json > /home/pi/PiWeatherRock/speedtest/queue/$(date +%s).json
