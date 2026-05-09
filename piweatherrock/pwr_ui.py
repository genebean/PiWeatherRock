#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Gene Liverman <gene@technicalissues.us>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import os
from argparse import ArgumentParser
from piweatherrock.runner import Runner


def main():
    parser = ArgumentParser(
        """Runs the PiWeatherRock UI""")
    parser.add_argument(
        '-c', '--config', required=True,
        help='Path to your config file')

    args = parser.parse_args()
    config = os.path.abspath(args.config)

    runner = Runner()
    runner.main(config)


if __name__ == '__main__':
    main()
