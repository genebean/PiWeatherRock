# -*- coding: utf-8 -*-
# Copyright (c) 2023 Carlos de Huerta <carlos.hm@live.com>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

from .forecast import Forecast


def forecast(key, latitude, longitude, time=None, timeout=None, **queries):
    return Forecast(key, latitude, longitude, time, timeout, **queries)
