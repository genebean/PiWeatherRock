# -*- coding: utf-8 -*-
# Copyright (c) 2021 Carlos de Huerta <carlos.hm@live.com>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import json
import babel

from datetime import date, datetime, time
from babel.dates import format_date, format_datetime, format_time
from os import path

RESOURCES_FILE = 'piweatherrock.lang.json'

class intl:
    """
    This class assists in the internationalization and localization Pi Weather Rock data
    through the text stored in the RESOURCES_FILE for different languages supported by the config file.
    and several methods for date and time information.
    """

    def __init__(self):       
        with open(path.join(path.dirname(__file__),RESOURCES_FILE), "r") as t:
            self.resources = json.load(t)
            
    def get_weekday(self, ui_lang, date):
        return format_date(date,"EEEE",locale='%s' % ui_lang).capitalize()
    
    def get_datetime(self, ui_lang, datetime, twelvehr):
        if twelvehr is True:
            return format_datetime(datetime, "EEE, MMM dd HH:mm", locale='%s' % ui_lang).title()
        else:
            return format_datetime(datetime, "EEE, MMM dd hh:mm", locale='%s' % ui_lang).title()

    def get_ampm(self, ui_lang, datetime):
        return format_datetime(datetime, "a", locale='%s' % ui_lang)
        
    def get_text(self, ui_lang, text, capital = False, fallback = 'en'):
        if self.resources.get(ui_lang) is None:
            ui_lang = fallback
            
        if capital is True:
            return self.resources[ui_lang][text].capitalize()
        else:
            return self.resources[ui_lang][text]