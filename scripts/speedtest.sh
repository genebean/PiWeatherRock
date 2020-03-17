#!/bin/bash

./scripts/speedtest-cli --json > speedtest/queue/$(date +%s).json
