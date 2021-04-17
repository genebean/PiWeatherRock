# -*- coding: utf-8 -*-
# Copyright (c) 2021 Carlos de Huerta <carlos.hm@live.com>
# Distributed under the MIT License (https://opensource.org/licenses/MIT)

import json
import babel
import i18n

from datetime import date, datetime, time
from babel.dates import format_date, format_datetime, format_time
from os import path

class intl:
    """
    This class assists in the internationalization and localization Pi Weather Rock data
    through the use of python i18n and Babel.
    """

    def __init__(self):       
        i18n.set('file_format', 'json')
        i18n.set('fallback', 'en')
        i18n.load_path.append(path.join(path.dirname(__file__),'data'))
            
    def get_weekday(self, ui_lang, date):
        return format_date(date,"EEEE",locale='%s' % ui_lang).capitalize()
    
    def get_datetime(self, ui_lang, datetime, twelvehr):
        if twelvehr is True:
            return format_datetime(datetime, "EEE, MMM dd HH:mm", locale='%s' % ui_lang).title()
        else:
            return format_datetime(datetime, "EEE, MMM dd hh:mm", locale='%s' % ui_lang).title()

    def get_ampm(self, ui_lang, datetime):
        return format_datetime(datetime, "a", locale='%s' % ui_lang)
        
    def get_text(self, ui_lang, text, params = None):
        i18n.set('locale', ui_lang)
        label = 'piweatherrock.' + text

        if params is None:
            return i18n.t(label)
        else:
            return i18n.t(label, **params)