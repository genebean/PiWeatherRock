#!/bin/bash

speedtest-cli --json > speedtest/queue/$(date +%s).json
