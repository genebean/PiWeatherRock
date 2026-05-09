#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local web configuration UI for PiWeatherRock."""

import html
import json
import os
import platform
import secrets
import shutil
import socket
import webbrowser
from argparse import ArgumentParser
from urllib.parse import urlencode
from urllib.request import urlopen

import cherrypy

from piweatherrock.config_manager import (
    CONFIG_FORM_FIELDS,
    ConfigError,
    MEDIA_FIT_MODES,
    expand_config_path,
    field_name,
    get_config_value,
    load_config,
    SUPPORTED_LANGUAGES,
    SUPPORTED_TIMEZONES,
    set_config_value,
    validate_config,
    write_config_atomic,
)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


TEXT = {
    'en': {
        'back_to_config': 'Back to configuration',
        'changes_applied': 'Changes applied',
        'config_error': 'Configuration error',
        'current_value_fallback': '{} (current value)',
        'error': 'Error',
        'invalid_request': 'Invalid request. Refresh the page and try again.',
        'legend': 'PiWeatherRock configuration',
        'location_custom': 'Custom coordinates',
        'location_preset': 'Quick location',
        'open_map': 'Open larger map',
        'map_hint': 'Move or zoom the map normally. Use the pin button only when you want to place the marker with a click.',
        'map_pick_active': 'Click the map to place the pin',
        'map_pick_start': 'Place pin on map',
        'map_title': 'Location map preview',
        'media_path_hint': 'Use an existing folder. Examples: /home/pi/Pictures, ~/Pictures, C:\\Users\\YourName\\Pictures, or your OneDrive Pictures folder. ~ and environment variables are expanded.',
        'plain_status': 'Plain status',
        'runtime_status': 'Runtime status',
        'save': 'Save changes',
        'status_ok': 'OK: valid configuration. The UI will apply changes automatically.',
        'subtitle': 'Adjust weather, display, rotation, and local media options from one guided form.',
        'test_weather': 'Test Open-Meteo',
        'test_weather_ok': 'Open-Meteo responded successfully.',
        'test_weather_title': 'Open-Meteo test',
        'title': 'PiWeatherRock Config',
        'validate': 'Validate configuration',
        'validate_details': 'Review configuration',
        'validation_title': 'Configuration validation',
        'rotation_global_title': 'Global controls',
        'rotation_global_help': 'These settings control the automatic info cycle used across the rotation.',
        'rotation_pages_title': 'Per-page visibility',
        'rotation_pages_help': 'Each enabled page uses its own duration before moving to the next page.',
        'labels': {
            'lat': 'Latitude',
            'lon': 'Longitude',
            'timezone': 'Timezone',
            'ds_api_key': 'Open-Meteo identifier',
            'units': 'Units',
            'lang': 'Weather language',
            'ui_lang': 'UI language',
            'update_freq': 'Forecast refresh interval (seconds)',
            'fullscreen': 'Fullscreen',
            '12hour_disp': '12-hour format',
            'icon_offset': 'Icon offset',
            'info_pause': 'Global info-cycle pause (seconds)',
            'info_delay': 'Global delay before automatic info page (seconds)',
            'daily_enabled': 'Daily page enabled',
            'daily_pause': 'Daily page visibility duration (seconds)',
            'hourly_enabled': 'Hourly page enabled',
            'hourly_pause': 'Hourly page visibility duration (seconds)',
            'info_enabled': 'Info page enabled',
            'info_pause_plugin': 'Info page visibility duration (seconds)',
            'media_enabled': 'Local media page enabled',
            'media_pause': 'Local media page visibility duration (seconds)',
            'media_path': 'Local media folder',
            'media_shuffle': 'Shuffle local media',
            'media_fit': 'Media fit',
            'media_extensions': 'Media extensions',
            'log_level': 'Log level'},
        'sections': {
            'location': 'Location and timezone',
            'weather': 'Weather and language',
            'display': 'Display',
            'rotation': 'Page rotation pauses',
            'media': 'Local media',
            'diagnostics': 'Diagnostics'},
        'help': {
            'location': 'Coordinates and timezone used for forecast, sunrise, and sunset calculations.',
            'weather': 'Open-Meteo request identifier, units, and languages shown in the weather and UI texts.',
            'display': 'Screen presentation options for the Raspberry Pi display.',
            'rotation': 'Global controls are grouped first; each enabled page below has its own visibility duration.',
            'media': 'Local folder, ordering, fit mode, and allowed image/video extensions.',
            'diagnostics': 'Logging verbosity for troubleshooting.'}},
    'es': {
        'back_to_config': 'Volver a la configuración',
        'changes_applied': 'Cambios aplicados',
        'config_error': 'Error de configuración',
        'current_value_fallback': '{} (valor actual)',
        'error': 'Error',
        'invalid_request': 'Solicitud no válida. Recarga la página e inténtalo de nuevo.',
        'legend': 'Configuración PiWeatherRock',
        'location_custom': 'Coordenadas personalizadas',
        'location_preset': 'Ubicación rápida',
        'open_map': 'Abrir mapa grande',
        'map_hint': 'Mueve o amplía el mapa normalmente. Usa el botón de chincheta solo cuando quieras colocar el marcador con un clic.',
        'map_pick_active': 'Haz clic en el mapa para colocar la chincheta',
        'map_pick_start': 'Colocar chincheta en el mapa',
        'map_title': 'Vista previa del mapa de ubicación',
        'media_path_hint': 'Usa una carpeta que exista. Ejemplos: /home/pi/Pictures, ~/Pictures, C:\\Users\\TuUsuario\\Pictures o tu carpeta Pictures de OneDrive. ~ y las variables de entorno se expanden.',
        'plain_status': 'Estado simple',
        'runtime_status': 'Estado de ejecución',
        'save': 'Guardar cambios',
        'status_ok': 'OK: configuración válida. La UI aplicará los cambios automáticamente.',
        'subtitle': 'Ajusta meteorología, pantalla, rotación y medios locales desde un formulario guiado.',
        'test_weather': 'Probar Open-Meteo',
        'test_weather_ok': 'Open-Meteo respondió correctamente.',
        'test_weather_title': 'Prueba de Open-Meteo',
        'title': 'Configuración de PiWeatherRock',
        'validate': 'Validar configuración',
        'validate_details': 'Revisar configuración',
        'validation_title': 'Validación de configuración',
        'rotation_global_title': 'Controles globales',
        'rotation_global_help': 'Estos ajustes controlan el ciclo automático de información usado en toda la rotación.',
        'rotation_pages_title': 'Visibilidad por página',
        'rotation_pages_help': 'Cada página activada usa su propia duración antes de pasar a la siguiente.',
        'labels': {
            'lat': 'Latitud',
            'lon': 'Longitud',
            'timezone': 'Zona horaria',
            'ds_api_key': 'Identificador Open-Meteo',
            'units': 'Unidades',
            'lang': 'Idioma meteorológico',
            'ui_lang': 'Idioma de interfaz',
            'update_freq': 'Intervalo de actualización del pronóstico (segundos)',
            'fullscreen': 'Pantalla completa',
            '12hour_disp': 'Formato de 12 horas',
            'icon_offset': 'Desplazamiento de iconos',
            'info_pause': 'Pausa global del ciclo de información (segundos)',
            'info_delay': 'Retraso global antes de mostrar información automática (segundos)',
            'daily_enabled': 'Página diaria activada',
            'daily_pause': 'Duración visible de página diaria (segundos)',
            'hourly_enabled': 'Página horaria activada',
            'hourly_pause': 'Duración visible de página horaria (segundos)',
            'info_enabled': 'Página de información activada',
            'info_pause_plugin': 'Duración visible de página de información (segundos)',
            'media_enabled': 'Página de medios locales activada',
            'media_pause': 'Duración visible de página de medios locales (segundos)',
            'media_path': 'Carpeta local de medios',
            'media_shuffle': 'Medios locales en orden aleatorio',
            'media_fit': 'Ajuste de medios',
            'media_extensions': 'Extensiones de medios',
            'log_level': 'Nivel de log'},
        'sections': {
            'location': 'Ubicación y zona horaria',
            'weather': 'Meteorología e idioma',
            'display': 'Pantalla',
            'rotation': 'Pausas de rotación de páginas',
            'media': 'Medios locales',
            'diagnostics': 'Diagnóstico'},
        'help': {
            'location': 'Coordenadas y zona horaria usadas para el pronóstico, amanecer y atardecer.',
            'weather': 'Identificador Open-Meteo, unidades e idiomas mostrados en la meteorología y la interfaz.',
            'display': 'Opciones de presentación para la pantalla de la Raspberry Pi.',
            'rotation': 'Los controles globales se agrupan primero; cada página activada debajo tiene su propia duración visible.',
            'media': 'Carpeta local, orden, modo de ajuste y extensiones de imagen/vídeo permitidas.',
            'diagnostics': 'Nivel de detalle de los registros para solucionar problemas.'}},
    'ca': {
        'back_to_config': 'Torna a la configuració',
        'changes_applied': 'Canvis aplicats',
        'config_error': 'Error de configuració',
        'current_value_fallback': '{} (valor actual)',
        'error': 'Error',
        'invalid_request': 'Sol·licitud no vàlida. Recarrega la pàgina i torna-ho a provar.',
        'legend': 'Configuració de PiWeatherRock',
        'location_custom': 'Coordenades personalitzades',
        'location_preset': 'Ubicació ràpida',
        'open_map': 'Obre el mapa gran',
        'map_hint': 'Mou o amplia el mapa normalment. Usa el botó de xinxeta només quan vulguis col·locar el marcador amb un clic.',
        'map_pick_active': 'Fes clic al mapa per col·locar la xinxeta',
        'map_pick_start': 'Col·loca xinxeta al mapa',
        'map_title': 'Vista prèvia del mapa d’ubicació',
        'media_path_hint': 'Usa una carpeta que existeixi. Exemples: /home/pi/Pictures, ~/Pictures, C:\\Users\\ElTeuUsuari\\Pictures o la carpeta Pictures de OneDrive. ~ i les variables d’entorn s’expandeixen.',
        'plain_status': 'Estat simple',
        'runtime_status': 'Estat d’execució',
        'save': 'Desa els canvis',
        'status_ok': 'OK: configuració vàlida. La UI aplicarà els canvis automàticament.',
        'subtitle': 'Ajusta meteorologia, pantalla, rotació i mitjans locals des d’un formulari guiat.',
        'test_weather': 'Prova Open-Meteo',
        'test_weather_ok': 'Open-Meteo ha respost correctament.',
        'test_weather_title': 'Prova d’Open-Meteo',
        'title': 'Configuració de PiWeatherRock',
        'validate': 'Valida la configuració',
        'validate_details': 'Revisa la configuració',
        'validation_title': 'Validació de la configuració',
        'rotation_global_title': 'Controls globals',
        'rotation_global_help': 'Aquests ajustos controlen el cicle automàtic d’informació usat en tota la rotació.',
        'rotation_pages_title': 'Visibilitat per pàgina',
        'rotation_pages_help': 'Cada pàgina activada usa la seva pròpia durada abans de passar a la següent.',
        'labels': {
            'lat': 'Latitud',
            'lon': 'Longitud',
            'timezone': 'Zona horària',
            'ds_api_key': 'Identificador Open-Meteo',
            'units': 'Unitats',
            'lang': 'Idioma meteorològic',
            'ui_lang': 'Idioma de la interfície',
            'update_freq': 'Interval d’actualització de la previsió (segons)',
            'fullscreen': 'Pantalla completa',
            '12hour_disp': 'Format de 12 hores',
            'icon_offset': 'Desplaçament de les icones',
            'info_pause': 'Pausa global del cicle d’informació (segons)',
            'info_delay': 'Retard global abans de mostrar informació automàtica (segons)',
            'daily_enabled': 'Pàgina diària activada',
            'daily_pause': 'Durada visible de pàgina diària (segons)',
            'hourly_enabled': 'Pàgina horària activada',
            'hourly_pause': 'Durada visible de pàgina horària (segons)',
            'info_enabled': 'Pàgina d’informació activada',
            'info_pause_plugin': 'Durada visible de pàgina d’informació (segons)',
            'media_enabled': 'Pàgina de mitjans locals activada',
            'media_pause': 'Durada visible de pàgina de mitjans locals (segons)',
            'media_path': 'Carpeta local de mitjans',
            'media_shuffle': 'Mitjans locals en ordre aleatori',
            'media_fit': 'Ajust de mitjans',
            'media_extensions': 'Extensions de mitjans',
            'log_level': 'Nivell de log'},
        'sections': {
            'location': 'Ubicació i zona horària',
            'weather': 'Meteorologia i idioma',
            'display': 'Pantalla',
            'rotation': 'Pauses de rotació de pàgines',
            'media': 'Mitjans locals',
            'diagnostics': 'Diagnòstic'},
        'help': {
            'location': 'Coordenades i zona horària usades per a la previsió, sortida i posta de sol.',
            'weather': 'Identificador Open-Meteo, unitats i idiomes mostrats a la meteorologia i la interfície.',
            'display': 'Opcions de presentació per a la pantalla de la Raspberry Pi.',
            'rotation': 'Els controls globals s’agrupen primer; cada pàgina activada a sota té la seva pròpia durada visible.',
            'media': 'Carpeta local, ordre, mode d’ajust i extensions d’imatge/vídeo permeses.',
            'diagnostics': 'Nivell de detall dels registres per resoldre problemes.'}},
    'gl': {
        'back_to_config': 'Volver á configuración',
        'changes_applied': 'Cambios aplicados',
        'config_error': 'Erro de configuración',
        'current_value_fallback': '{} (valor actual)',
        'error': 'Erro',
        'invalid_request': 'Solicitude non válida. Recarga a páxina e téntao de novo.',
        'legend': 'Configuración de PiWeatherRock',
        'location_custom': 'Coordenadas personalizadas',
        'location_preset': 'Localización rápida',
        'open_map': 'Abrir mapa grande',
        'map_hint': 'Move ou amplía o mapa normalmente. Usa o botón de chincheta só cando queiras colocar o marcador cun clic.',
        'map_pick_active': 'Fai clic no mapa para colocar a chincheta',
        'map_pick_start': 'Colocar chincheta no mapa',
        'map_title': 'Vista previa do mapa de localización',
        'media_path_hint': 'Usa un cartafol que exista. Exemplos: /home/pi/Pictures, ~/Pictures, C:\\Users\\OteuUsuario\\Pictures ou o teu cartafol Pictures de OneDrive. ~ e as variables de contorno expándense.',
        'plain_status': 'Estado simple',
        'runtime_status': 'Estado de execución',
        'save': 'Gardar cambios',
        'status_ok': 'OK: configuración válida. A UI aplicará os cambios automaticamente.',
        'subtitle': 'Axusta meteoroloxía, pantalla, rotación e medios locais desde un formulario guiado.',
        'test_weather': 'Probar Open-Meteo',
        'test_weather_ok': 'Open-Meteo respondeu correctamente.',
        'test_weather_title': 'Proba de Open-Meteo',
        'title': 'Configuración de PiWeatherRock',
        'validate': 'Validar configuración',
        'validate_details': 'Revisar configuración',
        'validation_title': 'Validación de configuración',
        'rotation_global_title': 'Controis globais',
        'rotation_global_help': 'Estes axustes controlan o ciclo automático de información usado en toda a rotación.',
        'rotation_pages_title': 'Visibilidade por páxina',
        'rotation_pages_help': 'Cada páxina activada usa a súa propia duración antes de pasar á seguinte.',
        'labels': {
            'lat': 'Latitude',
            'lon': 'Lonxitude',
            'timezone': 'Zona horaria',
            'ds_api_key': 'Identificador Open-Meteo',
            'units': 'Unidades',
            'lang': 'Idioma meteorolóxico',
            'ui_lang': 'Idioma da interface',
            'update_freq': 'Intervalo de actualización da predición (segundos)',
            'fullscreen': 'Pantalla completa',
            '12hour_disp': 'Formato de 12 horas',
            'icon_offset': 'Desprazamento das iconas',
            'info_pause': 'Pausa global do ciclo de información (segundos)',
            'info_delay': 'Retardo global antes de mostrar información automática (segundos)',
            'daily_enabled': 'Páxina diaria activada',
            'daily_pause': 'Duración visible da páxina diaria (segundos)',
            'hourly_enabled': 'Páxina horaria activada',
            'hourly_pause': 'Duración visible da páxina horaria (segundos)',
            'info_enabled': 'Páxina de información activada',
            'info_pause_plugin': 'Duración visible da páxina de información (segundos)',
            'media_enabled': 'Páxina de medios locais activada',
            'media_pause': 'Duración visible da páxina de medios locais (segundos)',
            'media_path': 'Cartafol local de medios',
            'media_shuffle': 'Medios locais en orde aleatoria',
            'media_fit': 'Axuste de medios',
            'media_extensions': 'Extensións de medios',
            'log_level': 'Nivel de log'},
        'sections': {
            'location': 'Localización e zona horaria',
            'weather': 'Meteoroloxía e idioma',
            'display': 'Pantalla',
            'rotation': 'Pausas de rotación de páxinas',
            'media': 'Medios locais',
            'diagnostics': 'Diagnóstico'},
        'help': {
            'location': 'Coordenadas e zona horaria usadas para a predición, amencer e solpor.',
            'weather': 'Identificador Open-Meteo, unidades e idiomas mostrados na meteoroloxía e na interface.',
            'display': 'Opcións de presentación para a pantalla da Raspberry Pi.',
            'rotation': 'Os controis globais agrúpanse primeiro; cada páxina activada debaixo ten a súa propia duración visible.',
            'media': 'Cartafol local, orde, modo de axuste e extensións de imaxe/vídeo permitidas.',
            'diagnostics': 'Nivel de detalle dos rexistros para resolver problemas.'}},
    'eu': {
        'back_to_config': 'Itzuli konfiguraziora',
        'changes_applied': 'Aldaketak aplikatu dira',
        'config_error': 'Konfigurazio-errorea',
        'current_value_fallback': '{} (uneko balioa)',
        'error': 'Errorea',
        'invalid_request': 'Eskaera ez da baliozkoa. Freskatu orria eta saiatu berriro.',
        'legend': 'PiWeatherRock konfigurazioa',
        'location_custom': 'Koordenatu pertsonalizatuak',
        'location_preset': 'Kokapen azkarra',
        'open_map': 'Ireki mapa handia',
        'map_hint': 'Mugitu edo handitu mapa normaltasunez. Erabili txintxeta botoia markatzailea klik batekin kokatu nahi duzunean bakarrik.',
        'map_pick_active': 'Egin klik mapan txintxeta kokatzeko',
        'map_pick_start': 'Kokatu txintxeta mapan',
        'map_title': 'Kokapen maparen aurrebista',
        'media_path_hint': 'Erabili existitzen den karpeta bat. Adibideak: /home/pi/Pictures, ~/Pictures, C:\\Users\\ZureErabiltzailea\\Pictures edo OneDriveko Pictures karpeta. ~ eta ingurune-aldagaiak hedatzen dira.',
        'plain_status': 'Egoera sinplea',
        'runtime_status': 'Exekuzio-egoera',
        'save': 'Gorde aldaketak',
        'status_ok': 'OK: konfigurazioa baliozkoa da. UIak aldaketak automatikoki aplikatuko ditu.',
        'subtitle': 'Eguraldia, pantaila, biraketa eta tokiko multimedia formulario gidatu batetik doitu.',
        'test_weather': 'Probatu Open-Meteo',
        'test_weather_ok': 'Open-Meteok behar bezala erantzun du.',
        'test_weather_title': 'Open-Meteo proba',
        'title': 'PiWeatherRock konfigurazioa',
        'validate': 'Balidatu konfigurazioa',
        'validate_details': 'Berrikusi konfigurazioa',
        'validation_title': 'Konfigurazioaren balidazioa',
        'rotation_global_title': 'Kontrol globalak',
        'rotation_global_help': 'Ezarpen hauek biraketa osoan erabiltzen den informazio-ziklo automatikoa kontrolatzen dute.',
        'rotation_pages_title': 'Orri bakoitzeko ikusgaitasuna',
        'rotation_pages_help': 'Gaitutako orri bakoitzak bere iraupena erabiltzen du hurrengora pasatu aurretik.',
        'labels': {
            'lat': 'Latitudea',
            'lon': 'Longitudea',
            'timezone': 'Ordu-zona',
            'ds_api_key': 'Open-Meteo identifikatzailea',
            'units': 'Unitateak',
            'lang': 'Eguraldiaren hizkuntza',
            'ui_lang': 'Interfazearen hizkuntza',
            'update_freq': 'Iragarpenaren eguneratze-tartea (segundoak)',
            'fullscreen': 'Pantaila osoa',
            '12hour_disp': '12 orduko formatua',
            'icon_offset': 'Ikonoen desplazamendua',
            'info_pause': 'Informazio-zikloaren pausa globala (segundoak)',
            'info_delay': 'Informazio automatikoa erakutsi aurreko atzerapen globala (segundoak)',
            'daily_enabled': 'Eguneko orria gaituta',
            'daily_pause': 'Eguneko orriaren ikusgai egoteko iraupena (segundoak)',
            'hourly_enabled': 'Orduko orria gaituta',
            'hourly_pause': 'Orduko orriaren ikusgai egoteko iraupena (segundoak)',
            'info_enabled': 'Informazio-orria gaituta',
            'info_pause_plugin': 'Informazio-orriaren ikusgai egoteko iraupena (segundoak)',
            'media_enabled': 'Tokiko multimedia-orria gaituta',
            'media_pause': 'Tokiko multimedia-orriaren ikusgai egoteko iraupena (segundoak)',
            'media_path': 'Tokiko multimedia-karpeta',
            'media_shuffle': 'Tokiko multimedia ausazko ordenan',
            'media_fit': 'Multimedia doitzea',
            'media_extensions': 'Multimedia-luzapenak',
            'log_level': 'Log-maila'},
        'sections': {
            'location': 'Kokapena eta ordu-zona',
            'weather': 'Eguraldia eta hizkuntza',
            'display': 'Pantaila',
            'rotation': 'Orrialde-biraketaren pausak',
            'media': 'Tokiko multimedia',
            'diagnostics': 'Diagnostikoa'},
        'help': {
            'location': 'Iragarpenerako, egunsentirako eta ilunabarrerako erabiltzen diren koordenatuak eta ordu-zona.',
            'weather': 'Open-Meteo identifikatzailea, unitateak eta eguraldian nahiz interfazean erakusten diren hizkuntzak.',
            'display': 'Raspberry Pi pantailarako aurkezpen-aukerak.',
            'rotation': 'Kontrol globalak lehenik taldekatzen dira; beheko gaitutako orri bakoitzak bere ikusgai egoteko iraupena du.',
            'media': 'Tokiko karpeta, ordena, doitze-modua eta baimendutako irudi/bideo luzapenak.',
            'diagnostics': 'Arazoak konpontzeko erregistroen xehetasun-maila.'}}
}


FORM_SECTIONS = [
    ('location', (('lat',), ('lon',), ('timezone',))),
    ('weather', (('ds_api_key',), ('units',), ('lang',), ('ui_lang',), ('update_freq',))),
    ('display', (('fullscreen',), ('12hour_disp',), ('icon_offset',))),
    ('rotation', (
        ('info_pause',), ('info_delay',),
        ('plugins', 'daily', 'enabled'), ('plugins', 'daily', 'pause'),
        ('plugins', 'hourly', 'enabled'), ('plugins', 'hourly', 'pause'),
        ('plugins', 'info', 'enabled'), ('plugins', 'info', 'pause'),
        ('plugins', 'media', 'enabled'), ('plugins', 'media', 'pause'))),
    ('media', (
        ('plugins', 'media', 'path'), ('plugins', 'media', 'shuffle'),
        ('plugins', 'media', 'fit'), ('plugins', 'media', 'extensions'))),
    ('diagnostics', (('log_level',),)),
]

ROTATION_GLOBAL_FIELDS = (('info_pause',), ('info_delay',))
ROTATION_PAGE_FIELDS = (
    ('plugins', 'daily', 'enabled'), ('plugins', 'daily', 'pause'),
    ('plugins', 'hourly', 'enabled'), ('plugins', 'hourly', 'pause'),
    ('plugins', 'info', 'enabled'), ('plugins', 'info', 'pause'),
    ('plugins', 'media', 'enabled'), ('plugins', 'media', 'pause'),
)

MAP_ZOOM_DELTA = 0.03
COORDINATE_PRECISION = 6
_TIMEZONE_OPTIONS = None

SELECT_OPTIONS = {
    ('units',): [('si', 'Metric (SI)'), ('us', 'US'), ('ca', 'Canada'),
                 ('uk2', 'UK'), ('auto', 'Auto')],
    ('lang',): [(language, language.upper()) for language in SUPPORTED_LANGUAGES],
    ('ui_lang',): [(language, language.upper()) for language in SUPPORTED_LANGUAGES],
    ('plugins', 'media', 'fit'): [(mode, mode.title()) for mode in MEDIA_FIT_MODES],
    ('log_level',): [(level, level) for level in
                     ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')],
}

LOCATION_PRESETS = (
    # Common launch locations for supported languages plus a few global examples.
    ('Getafe', 40.308250, -3.732393),
    ('Madrid', 40.416775, -3.703790),
    ('Barcelona', 41.387397, 2.168568),
    ('Valencia', 39.469907, -0.376288),
    ('Sevilla', 37.389092, -5.984459),
    ('Bilbao', 43.263013, -2.934985),
    ('A Coruña', 43.362344, -8.411540),
    ('London', 51.507351, -0.127758),
    ('Paris', 48.856613, 2.352222),
    ('Lisboa', 38.722252, -9.139337),
    ('New York', 40.712776, -74.005974),
)



class ConfigWebApp:
    def __init__(self, config_file):
        self.config_file = config_file
        self.csrf_token = secrets.token_urlsafe(32)

    @cherrypy.expose
    def index(self, saved="", **_ignored):
        self._set_no_store_headers()
        try:
            config = load_config(self.config_file)
            message = self._text(config, "changes_applied") if saved == "1" else ""
            body = self._render_form(config, message)
        except ConfigError as exc:
            body = self._page(TEXT["en"]["config_error"],
                              "<p>{}</p>".format(html.escape(str(exc))))
        return body

    @cherrypy.expose
    def save(self, **params):
        self._set_no_store_headers()
        try:
            config = load_config(self.config_file)
            if not self._valid_save_request(config, params):
                self._set_response_status(403)
                return self._render_form(
                    config, "Error: {}".format(
                        self._text(config, "invalid_request")))
            for path, label_key, field_type in CONFIG_FORM_FIELDS:
                name = field_name(path)
                value = self._coerce_value(params.get(name), field_type)
                set_config_value(config, path, value)
            validate_config(config)
            write_config_atomic(self.config_file, config)
            raise cherrypy.HTTPRedirect("/?saved=1")
        except (ConfigError, ValueError) as exc:
            try:
                config = load_config(self.config_file)
                return self._render_form(config, "Error: {}".format(exc))
            except ConfigError:
                return self._page(TEXT["en"]["error"], "<p>{}</p>".format(
                    html.escape(str(exc))))

    @cherrypy.expose
    def status(self):
        self._set_no_store_headers()
        try:
            config = load_config(self.config_file)
            return self._text(config, "status_ok")
        except ConfigError as exc:
            self._set_response_status(400)
            return "ERROR: {}".format(exc)

    @cherrypy.expose
    def validate(self):
        self._set_no_store_headers()
        try:
            config = load_config(self.config_file)
            body = self._render_validation(config)
            language = self._language(config)
        except ConfigError as exc:
            language = "en"
            body = self._render_status_items(
                [(False, TEXT["en"]["config_error"], str(exc))], language)
        body += self._back_link(language)
        return self._page(self._text_for_language(language, "validation_title"),
                          body, language)

    @cherrypy.expose
    def test_weather(self):
        self._set_no_store_headers()
        try:
            config = load_config(self.config_file)
            language = self._language(config)
            body = self._render_weather_test(config, language)
        except ConfigError as exc:
            language = "en"
            body = self._render_status_items(
                [(False, TEXT["en"]["config_error"], str(exc))], language)
        body += self._back_link(language)
        return self._page(self._text_for_language(language, "test_weather_title"),
                          body, language)

    def _render_form(self, config, message=""):
        rows = []
        if message:
            rows.append('<p class="message">{}</p>'.format(html.escape(message)))
        rows.append('<form method="post" action="/save">')
        rows.append('<input type="hidden" name="csrf_token" value="{}">'.format(
            html.escape(self.csrf_token, quote=True)))
        rows.append('<div class="sections">')
        for section_key, paths in FORM_SECTIONS:
            rows.append('<section class="card" aria-labelledby="{0}-title">'.format(
                html.escape(section_key)))
            rows.append('<div class="section-heading">')
            rows.append('<h2 id="{id}-title">{title}</h2>'.format(
                id=html.escape(section_key),
                title=html.escape(self._section_title(config, section_key))))
            rows.append('<span class="help-icon" tabindex="0" role="button" '
                        'aria-label="{help}" data-tooltip="{help}">'
                        '<span aria-hidden="true">?</span></span>'.format(
                            help=html.escape(
                                self._section_help(config, section_key),
                                quote=True)))
            rows.append('</div>')
            rows.append('<p class="section-help">{}</p>'.format(html.escape(
                self._section_help(config, section_key))))
            if section_key == 'location':
                rows.append('<div class="location-layout">')
                rows.append('<div class="location-controls">')
                rows.append('<div class="field-grid location-field-grid">')
                for path in paths:
                    rows.append(self._render_field(config, path))
                rows.append('</div>')
                rows.append(self._render_location_controls(config))
                rows.append('</div>')
                rows.append(self._render_location_map(config))
                rows.append('</div>')
            elif section_key == 'rotation':
                rows.append(self._render_rotation_fields(config))
            else:
                grid_class = (
                    "field-grid media-grid"
                    if section_key == 'media' else "field-grid")
                rows.append('<div class="{}">'.format(grid_class))
                for path in paths:
                    rows.append(self._render_field(config, path))
                rows.append('</div>')
            rows.append('</section>')
        rows.append('</div>')
        rows.append('<div class="actions"><button type="submit">{}</button>'.format(
            html.escape(self._text(config, "save"))))
        rows.append('<a class="button-link" href="/validate">{}</a>'.format(
            html.escape(self._text(config, "validate_details"))))
        rows.append('<a class="button-link" href="/test_weather">{}</a>'.format(
            html.escape(self._text(config, "test_weather"))))
        rows.append('<a class="status-link" href="/status">{}</a></div>'.format(
            html.escape(self._text(config, "plain_status"))))
        rows.append('</form>')
        return self._page(self._text(config, "title"), "\n".join(rows),
                          self._language(config))

    def _render_rotation_fields(self, config):
        return """<div class="section-subgroup">
  <h3>{global_title}</h3>
  <p>{global_help}</p>
  <div class="field-grid">{global_fields}</div>
</div>
<div class="section-subgroup">
  <h3>{pages_title}</h3>
  <p>{pages_help}</p>
  <div class="field-grid">{page_fields}</div>
</div>""".format(
            global_title=html.escape(self._text(config, "rotation_global_title")),
            global_help=html.escape(self._text(config, "rotation_global_help")),
            global_fields="".join(
                self._render_field(config, path) for path in ROTATION_GLOBAL_FIELDS),
            pages_title=html.escape(self._text(config, "rotation_pages_title")),
            pages_help=html.escape(self._text(config, "rotation_pages_help")),
            page_fields="".join(
                self._render_field(config, path) for path in ROTATION_PAGE_FIELDS))

    def _render_validation(self, config):
        checks = [
            (True, "Configuration file", self.config_file),
            (True, "Platform", "{} / Python {}".format(
                platform.system(), platform.python_version())),
        ]
        ffmpeg = shutil.which("ffmpeg")
        checks.append((
            bool(ffmpeg),
            "ffmpeg",
            ffmpeg or "Not found on PATH; local video playback will show a warning."))

        media_config = config.get("plugins", {}).get("media", {})
        media_path = media_config.get("path", "")
        expanded_media_path = expand_config_path(media_path) if media_path else ""
        if media_config.get("enabled"):
            checks.append((
                bool(expanded_media_path and os.path.isdir(expanded_media_path)),
                "Local media folder",
                expanded_media_path or "Missing path for enabled media page."))
        else:
            checks.append((
                None,
                "Local media folder",
                "Media page disabled; folder existence is not required."))

        return self._render_status_items(checks, self._language(config))

    def _render_weather_test(self, config, language):
        params = {
            "latitude": config["lat"],
            "longitude": config["lon"],
            "timezone": config["timezone"],
            "forecast_days": 1,
            "current_weather": "true",
        }
        url = OPEN_METEO_FORECAST_URL + "?" + urlencode(params)
        try:
            with urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if "current_weather" not in payload:
                raise ValueError("Open-Meteo response did not include current_weather")
            weather = payload["current_weather"]
            detail = "{} Temperature: {}. Wind: {}.".format(
                self._text_for_language(language, "test_weather_ok"),
                weather.get("temperature", "n/a"),
                weather.get("windspeed", "n/a"))
            checks = [(True, "Open-Meteo", detail)]
        except Exception as exc:
            checks = [(False, "Open-Meteo", str(exc))]
        return self._render_status_items(checks, language)

    def _valid_save_request(self, config, params):
        request = getattr(cherrypy, "request", None)
        method = getattr(request, "method", "POST")
        if method != "POST":
            return False
        return secrets.compare_digest(
            params.get("csrf_token", ""),
            self.csrf_token)

    def _render_status_items(self, checks, language):
        rows = ['<div class="status-panel">']
        rows.append('<h2>{}</h2>'.format(html.escape(
            self._text_for_language(language, "runtime_status"))))
        rows.append('<ul class="status-list">')
        for ok, label, detail in checks:
            status_class = "warn" if ok is None else "ok" if ok else "fail"
            status_text = "WARN" if ok is None else "OK" if ok else "ERROR"
            rows.append(
                '<li class="{status_class}"><strong>{label}</strong>'
                '<span class="status-badge">{status_text}</span>'
                '<p>{detail}</p></li>'.format(
                    status_class=status_class,
                    label=html.escape(label),
                    status_text=status_text,
                    detail=html.escape(str(detail))))
        rows.append('</ul></div>')
        return "\n".join(rows)

    def _back_link(self, language):
        return '<p><a class="button-link" href="/">{}</a></p>'.format(
            html.escape(self._text_for_language(language, "back_to_config")))

    def _field_hint(self, config, path):
        if path == ('plugins', 'media', 'path'):
            return self._text(config, "media_path_hint")
        return ""

    def _render_field(self, config, path):
        label_key, field_type = self._field_definition(path)
        value = get_config_value(config, path)
        name = field_name(path)
        escaped_name = html.escape(name)
        label = html.escape(self._label(config, label_key))
        control = ''
        if field_type == "bool":
            checked = " checked" if value else ""
            control = ('<label class="toggle"><input type="checkbox" '
                       'id="{name}" name="{name}" value="true"{checked}>'
                       '<span>{label}</span></label>').format(
                           name=escaped_name, checked=checked, label=label)
            return '<div class="field field-checkbox">{}</div>'.format(control)
        if path in SELECT_OPTIONS:
            control = self._render_select(config, path, value)
        elif path == ('timezone',):
            control = self._render_select(config, path, value)
        else:
            input_type = "number" if field_type in ("int", "float") else "text"
            step = ' step="any"' if field_type == "float" else ""
            control = ('<input type="{type}" id="{name}" name="{name}" '
                       'value="{value}"{step}>').format(
                           type=input_type,
                           name=escaped_name,
                           value=html.escape(str(value), quote=True),
                           step=step)
        hint = self._field_hint(config, path)
        hint_html = (
            '<p class="field-hint">{}</p>'.format(html.escape(hint))
            if hint else "")
        return ('<div class="field"><label for="{name}">{label}</label>'
                '{control}{hint}</div>').format(
                    name=escaped_name, label=label, control=control,
                    hint=hint_html)

    def _render_select(self, config, path, value):
        name = field_name(path)
        options = list(self._select_options(path))
        option_values = [option_value for option_value, _ in options]
        if value not in option_values:
            options.insert(0, (value, self._text(
                config, "current_value_fallback").format(value)))
        option_html = []
        for option_value, option_label in options:
            selected = " selected" if option_value == value else ""
            option_html.append(
                '<option value="{value}"{selected}>{label}</option>'.format(
                    value=html.escape(str(option_value), quote=True),
                    selected=selected,
                    label=html.escape(str(option_label))))
        return '<select id="{0}" name="{0}">{1}</select>'.format(
            html.escape(name), "".join(option_html))

    def _render_location_controls(self, config):
        lat = float(get_config_value(config, ("lat",)))
        lon = float(get_config_value(config, ("lon",)))
        open_url = 'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}'.format(
            lat=lat, lon=lon)
        return """<div class="map-copy">
    <strong>{title}</strong>
    <span>{hint}</span>
    <label for="location-preset">{preset_label}</label>
    <select id="location-preset" name="location-preset">
      <option value="">{custom_label}</option>
      {preset_options}
    </select>
    <button type="button" id="map-pick-toggle" class="map-pick-toggle"
            data-start="{pick_start}" data-active="{pick_active}">
      &#128204; {pick_start}
    </button>
    <a id="open-map-link" href="{open_url}" target="_blank" rel="noopener">{open_map}</a>
</div>""".format(
            title=html.escape(self._text(config, "map_title"), quote=True),
            hint=html.escape(self._text(config, "map_hint")),
            preset_label=html.escape(self._text(config, "location_preset")),
            custom_label=html.escape(self._text(config, "location_custom")),
            preset_options=self._render_location_preset_options(lat, lon),
            pick_start=html.escape(self._text(config, "map_pick_start")),
            pick_active=html.escape(self._text(config, "map_pick_active")),
            open_map=html.escape(self._text(config, "open_map")),
            open_url=html.escape(open_url, quote=True))

    def _render_location_map(self, config):
        lat = float(get_config_value(config, ("lat",)))
        lon = float(get_config_value(config, ("lon",)))
        map_url = self._map_url(lat, lon)
        return """<div class="map-panel">
  <iframe id="location-map" title="{title}" src="{map_url}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
  <button type="button" id="map-picker" class="map-picker" aria-label="{pick_active}"></button>
</div>""".format(
            title=html.escape(self._text(config, "map_title"), quote=True),
            pick_active=html.escape(self._text(config, "map_pick_active"), quote=True),
            map_url=html.escape(map_url, quote=True))

    def _render_location_preset_options(self, current_lat, current_lon):
        options = []
        for label, lat, lon in LOCATION_PRESETS:
            selected = " selected" if self._same_coordinate_pair(
                current_lat, current_lon, lat, lon) else ""
            options.append(
                '<option value="{lat},{lon}"{selected}>{label}</option>'.format(
                    lat=html.escape(str(lat), quote=True),
                    lon=html.escape(str(lon), quote=True),
                    selected=selected,
                    label=html.escape(label)))
        return "\n      ".join(options)

    def _same_coordinate_pair(self, first_lat, first_lon, second_lat, second_lon):
        first = (
            round(first_lat, COORDINATE_PRECISION),
            round(first_lon, COORDINATE_PRECISION),
        )
        second = (
            round(second_lat, COORDINATE_PRECISION),
            round(second_lon, COORDINATE_PRECISION),
        )
        return first == second

    def _page(self, title, body, language="en"):
        return """<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f3f6fb;
      --card: #ffffff;
      --text: #162033;
      --muted: #5d6b82;
      --brand: #2563eb;
      --brand-dark: #1d4ed8;
      --border: #dbe3ef;
      --shadow: 0 18px 45px rgba(22, 32, 51, .10);
      --input-bg: #fbfdff;
      --input-border: #cbd5e1;
      --toggle-bg: #f8fbff;
      --map-bg: #f8fbff;
      --help-bg: #eef4ff;
      --help-border: #bfdbfe;
      --hero-from: #1e3a8a;
      --hero-to: #2563eb;
      --msg-bg: #ecfdf5;
      --msg-border: #86efac;
      --msg-text: #14532d;
      --label-color: #26364d;
      --body-gradient: linear-gradient(135deg, #eaf2ff 0%, var(--bg) 42%, #f8fbff 100%);
    }}
    [data-theme="dark"] {{
      --bg: #0f172a;
      --card: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --brand: #3b82f6;
      --brand-dark: #60a5fa;
      --border: #334155;
      --shadow: 0 18px 45px rgba(0, 0, 0, .35);
      --input-bg: #0f172a;
      --input-border: #475569;
      --toggle-bg: #1e293b;
      --map-bg: #1e293b;
      --help-bg: #1e3a5f;
      --help-border: #1d4ed8;
      --hero-from: #0f172a;
      --hero-to: #1e40af;
      --msg-bg: #064e3b;
      --msg-border: #059669;
      --msg-text: #a7f3d0;
      --label-color: #cbd5e1;
      --body-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 42%, #0f172a 100%);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--body-gradient);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      min-height: 100vh;
      transition: background .3s, color .3s;
    }}
    main {{ margin: 0 auto; max-width: 74rem; padding: 2rem; }}
    .hero {{
      background: linear-gradient(135deg, var(--hero-from), var(--hero-to));
      border-radius: 1.4rem;
      box-shadow: var(--shadow);
      color: white;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 1.5rem;
      padding: 2rem;
    }}
    .hero-text {{ flex: 1; }}
    h1 {{ font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1; margin: 0 0 .65rem; }}
    .subtitle {{ color: rgba(255,255,255,.84); font-size: 1.05rem; margin: 0; max-width: 48rem; }}
    .theme-toggle {{
      background: rgba(255, 255, 255, .15);
      border: 1px solid rgba(255, 255, 255, .3);
      border-radius: .7rem;
      color: white;
      cursor: pointer;
      font-size: 1.3rem;
      line-height: 1;
      padding: .5rem .65rem;
      transition: background .2s;
    }}
    .theme-toggle:hover {{ background: rgba(255, 255, 255, .25); }}
    .sections {{ display: grid; gap: 1.1rem; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 1rem;
      box-shadow: 0 10px 30px rgba(22, 32, 51, .06);
      padding: 1.25rem;
      transition: background .3s, border-color .3s;
    }}
    .section-heading {{ align-items: center; display: flex; gap: .65rem; justify-content: space-between; }}
    h2 {{ font-size: 1.15rem; margin: 0; }}
    .help-icon {{
      align-items: center;
      background: var(--help-bg);
      border: 1px solid var(--help-border);
      border-radius: 999px;
      color: var(--brand);
      cursor: pointer;
      display: inline-flex;
      font-weight: 800;
      gap: .15rem;
      height: 1.65rem;
      justify-content: center;
      position: relative;
      width: 1.65rem;
    }}
    .help-icon::after {{
      background: var(--card);
      border: 1px solid var(--help-border);
      border-radius: .7rem;
      box-shadow: var(--shadow);
      color: var(--text);
      content: attr(data-tooltip);
      font-size: .92rem;
      font-weight: 600;
      line-height: 1.35;
      opacity: 0;
      padding: .9rem 1rem;
      pointer-events: none;
      position: absolute;
      right: 0;
      text-align: left;
      top: calc(100% + .55rem);
      transform: translateY(-.25rem);
      transition: opacity .15s, transform .15s;
      visibility: hidden;
      width: min(22rem, 75vw);
      z-index: 20;
    }}
    .help-icon:hover::after,
    .help-icon:focus::after {{
      opacity: 1;
      transform: translateY(0);
      visibility: visible;
    }}
    .section-help {{ color: var(--muted); margin: .45rem 0 1rem; }}
    .section-subgroup {{
      border-top: 1px solid var(--border);
      margin-top: 1rem;
      padding-top: 1rem;
    }}
    .section-subgroup:first-of-type {{ border-top: 0; margin-top: 0; padding-top: 0; }}
    h3 {{ font-size: 1rem; margin: 0 0 .35rem; }}
    .section-subgroup p, .field-hint {{ color: var(--muted); margin: 0 0 .85rem; }}
    .field-hint {{ font-size: .84rem; margin: .35rem 0 0; }}
    .field-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); }}
    .media-grid {{ align-items: start; grid-template-columns: repeat(2, minmax(14rem, 1fr)); }}
    .media-grid .field:first-child,
    .media-grid .field:last-child {{ grid-column: 1 / -1; }}
    .media-grid .field-checkbox {{
      align-items: start;
      min-height: auto;
      padding-top: 1.55rem;
    }}
    .media-grid .toggle {{ min-height: 3rem; }}
    label {{ color: var(--label-color); display: block; font-size: .92rem; font-weight: 700; margin-bottom: .35rem; }}
    input, select {{
      background: var(--input-bg);
      border: 1px solid var(--input-border);
      border-radius: .7rem;
      color: var(--text);
      font: inherit;
      padding: .72rem .85rem;
      transition: border-color .15s, box-shadow .15s, background .3s;
      width: 100%;
    }}
    input:focus, select:focus {{
      border-color: var(--brand);
      box-shadow: 0 0 0 .22rem rgba(37, 99, 235, .16);
      outline: none;
    }}
    .field-checkbox {{ align-items: end; display: flex; min-height: 4.4rem; }}
    .toggle {{
      align-items: center;
      background: var(--toggle-bg);
      border: 1px solid var(--border);
      border-radius: .8rem;
      cursor: pointer;
      display: flex;
      gap: .7rem;
      margin: 0;
      padding: .75rem .85rem;
      width: 100%;
    }}
    .toggle input {{ accent-color: var(--brand); height: 1.1rem; width: 1.1rem; }}
    .location-layout {{
      align-items: stretch;
      display: grid;
      gap: 1rem;
      grid-template-columns: minmax(16rem, 22rem) minmax(0, 1fr);
    }}
    .location-controls {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .location-field-grid {{ grid-template-columns: 1fr; }}
    .map-panel {{
      border: 1px solid var(--border);
      border-radius: .9rem;
      min-height: 30rem;
      overflow: hidden;
      position: relative;
    }}
    .map-copy {{ background: var(--map-bg); display: flex; flex-direction: column; gap: .5rem; padding: 1rem; }}
    .map-copy span {{ color: var(--muted); }}
    .map-copy a, .status-link {{ color: var(--brand); font-weight: 700; text-decoration: none; }}
    .map-pick-toggle {{
      background: var(--brand);
      border: 0;
      border-radius: .7rem;
      color: white;
      cursor: pointer;
      font: inherit;
      font-weight: 800;
      padding: .72rem .85rem;
      text-align: left;
      width: 100%;
    }}
    .map-pick-toggle.active {{ background: #dc2626; }}
    iframe {{ border: 0; min-height: 16rem; width: 100%; }}
    .map-panel iframe {{ height: 100%; min-height: 30rem; }}
    .actions {{ align-items: center; display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1.5rem; }}
    button {{
      background: var(--brand);
      border: 0;
      border-radius: .8rem;
      color: white;
      cursor: pointer;
      font: inherit;
      font-weight: 800;
      padding: .85rem 1.2rem;
      transition: background .2s;
    }}
    button:hover {{ background: var(--brand-dark); }}
    .map-picker {{
      background: transparent;
      border: 0;
      border-radius: 0;
      cursor: crosshair;
      inset: 0;
      padding: 0;
      pointer-events: none;
      position: absolute;
      width: auto;
    }}
    .map-panel.picking .map-picker {{ pointer-events: auto; }}
    .map-picker:hover {{ background: rgba(37, 99, 235, .04); }}
    .map-panel.picking .map-picker::after {{
      background: rgba(22, 32, 51, .78);
      border-radius: 999px;
      color: white;
      content: "\\1F4CC";
      font-size: 2rem;
      left: 50%;
      line-height: 1;
      padding: .55rem;
      position: absolute;
      top: 50%;
      transform: translate(-50%, -50%);
    }}
    .button-link {{
      background: transparent;
      border: 1px solid var(--brand);
      border-radius: .8rem;
      color: var(--brand);
      display: inline-block;
      font-weight: 800;
      padding: .78rem 1.05rem;
      text-decoration: none;
    }}
    .button-link:hover {{ background: rgba(37, 99, 235, .10); }}
    .message {{
      background: var(--msg-bg);
      border: 1px solid var(--msg-border);
      border-radius: .8rem;
      color: var(--msg-text);
      padding: .9rem 1rem;
    }}
    .status-panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 1rem;
      box-shadow: 0 10px 30px rgba(22, 32, 51, .06);
      padding: 1.25rem;
    }}
    .status-list {{ display: grid; gap: .8rem; list-style: none; margin: 1rem 0 0; padding: 0; }}
    .status-list li {{
      border: 1px solid var(--border);
      border-left-width: .35rem;
      border-radius: .8rem;
      padding: .85rem;
    }}
    .status-list li.ok {{ border-left-color: #16a34a; }}
    .status-list li.warn {{ border-left-color: #eab308; }}
    .status-list li.fail {{ border-left-color: #dc2626; }}
    .status-list p {{ color: var(--muted); margin: .35rem 0 0; }}
    .status-badge {{
      border: 1px solid var(--border);
      border-radius: 999px;
      float: right;
      font-size: .76rem;
      font-weight: 800;
      padding: .15rem .5rem;
    }}
    @media (max-width: 720px) {{
      main {{ padding: 1rem; }}
      .hero {{ padding: 1.4rem; flex-direction: column; gap: 1rem; }}
      .location-layout,
      .media-grid {{ grid-template-columns: 1fr; }}
      .media-grid .field:first-child,
      .media-grid .field:last-child {{ grid-column: auto; }}
      .media-grid .field-checkbox {{ padding-top: 0; }}
      .map-panel, .map-panel iframe {{ min-height: 22rem; }}
    }}
    @media (prefers-color-scheme: dark) {{
      html:not([data-theme="light"]) {{
        --bg: #0f172a;
        --card: #1e293b;
        --text: #e2e8f0;
        --muted: #94a3b8;
        --brand: #3b82f6;
        --brand-dark: #60a5fa;
        --border: #334155;
        --shadow: 0 18px 45px rgba(0, 0, 0, .35);
        --input-bg: #0f172a;
        --input-border: #475569;
        --toggle-bg: #1e293b;
        --map-bg: #1e293b;
        --help-bg: #1e3a5f;
        --help-border: #1d4ed8;
        --hero-from: #0f172a;
        --hero-to: #1e40af;
        --msg-bg: #064e3b;
        --msg-border: #059669;
        --msg-text: #a7f3d0;
        --label-color: #cbd5e1;
        --body-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 42%, #0f172a 100%);
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div class="hero-text">
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
      </div>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">&#9790;</button>
    </header>
    {body}
  </main>
  <script>
    (function () {{
      var toggle = document.getElementById('theme-toggle');
      var html = document.documentElement;
      var stored = localStorage.getItem('pwr-theme');
      if (stored) {{
        html.setAttribute('data-theme', stored);
      }}
      function updateIcon() {{
        var theme = html.getAttribute('data-theme');
        toggle.textContent = theme === 'dark' ? '\\u2600' : '\\u263E';
      }}
      updateIcon();
      toggle.addEventListener('click', function () {{
        var current = html.getAttribute('data-theme');
        var next = current === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('pwr-theme', next);
        updateIcon();
      }});
      var lat = document.getElementById('lat');
      var lon = document.getElementById('lon');
      var frame = document.getElementById('location-map');
      var link = document.getElementById('open-map-link');
      var preset = document.getElementById('location-preset');
      var picker = document.getElementById('map-picker');
      var pickToggle = document.getElementById('map-pick-toggle');
      var mapPanel = picker ? picker.closest('.map-panel') : null;
      function mapUrl(latitude, longitude) {{
        var delta = {map_delta};
        var left = longitude - delta;
        var right = longitude + delta;
        var top = latitude + delta;
        var bottom = latitude - delta;
        return 'https://www.openstreetmap.org/export/embed.html?bbox=' +
          encodeURIComponent(left + ',' + bottom + ',' + right + ',' + top) +
          '&layer=mapnik&marker=' +
          encodeURIComponent(latitude + ',' + longitude);
      }}
      function updateMap() {{
        var latitude = parseFloat(lat.value);
        var longitude = parseFloat(lon.value);
        if (isNaN(latitude) || isNaN(longitude) || !frame || !link) {{
          return;
        }}
        frame.src = mapUrl(latitude, longitude);
        link.href = 'https://www.openstreetmap.org/?mlat=' + encodeURIComponent(latitude) +
          '&mlon=' + encodeURIComponent(longitude) + '#map=12/' +
          encodeURIComponent(latitude) + '/' + encodeURIComponent(longitude);
      }}
      function setPickedLocation(latitude, longitude) {{
        lat.value = latitude.toFixed(6);
        lon.value = longitude.toFixed(6);
        if (preset) {{
          preset.value = '';
        }}
        updateMap();
      }}
      function setPickMode(active) {{
        if (!pickToggle || !mapPanel) {{
          return;
        }}
        mapPanel.classList.toggle('picking', active);
        pickToggle.classList.toggle('active', active);
        pickToggle.textContent = (active ? '\\uD83D\\uDCCC ' + pickToggle.dataset.active : '\\uD83D\\uDCCC ' + pickToggle.dataset.start);
      }}
      if (lat && lon && frame && link) {{
        lat.addEventListener('change', updateMap);
        lon.addEventListener('change', updateMap);
        if (pickToggle) {{
          pickToggle.addEventListener('click', function () {{
            setPickMode(!(mapPanel && mapPanel.classList.contains('picking')));
          }});
        }}
        if (picker) {{
          picker.addEventListener('click', function (event) {{
            if (!mapPanel || !mapPanel.classList.contains('picking')) {{
              return;
            }}
            var centerLat = parseFloat(lat.value);
            var centerLon = parseFloat(lon.value);
            if (isNaN(centerLat) || isNaN(centerLon)) {{
              return;
            }}
            var rect = picker.getBoundingClientRect();
            var delta = {map_delta};
            var clickX = (event.clientX - rect.left) / rect.width;
            var clickY = (event.clientY - rect.top) / rect.height;
            var pickedLon = centerLon - delta + (clickX * delta * 2);
            var pickedLat = centerLat + delta - (clickY * delta * 2);
            setPickedLocation(pickedLat, pickedLon);
            setPickMode(false);
          }});
        }}
        if (preset) {{
          preset.addEventListener('change', function () {{
            if (!preset.value) {{
              return;
            }}
            var parts = preset.value.split(',');
            lat.value = parts[0];
            lon.value = parts[1];
            updateMap();
          }});
        }}
      }}
    }}());
  </script>
</body>
</html>""".format(
            language=html.escape(language),
            title=html.escape(title),
            subtitle=html.escape(TEXT.get(language, TEXT["en"])["subtitle"]),
            map_delta=MAP_ZOOM_DELTA,
            body=body)

    def _section_title(self, config, key):
        language = self._language(config)
        return TEXT.get(language, TEXT["en"])["sections"][key]

    def _section_help(self, config, key):
        language = self._language(config)
        return TEXT.get(language, TEXT["en"])["help"][key]

    def _map_url(self, lat, lon):
        delta = MAP_ZOOM_DELTA
        bbox = "{},{},{},{}".format(lon - delta, lat - delta, lon + delta, lat + delta)
        return "https://www.openstreetmap.org/export/embed.html?" + urlencode({
            "bbox": bbox,
            "layer": "mapnik",
            "marker": "{},{}".format(lat, lon),
        })

    def _coerce_value(self, raw_value, field_type):
        if field_type == "bool":
            return raw_value == "true"
        if raw_value is None:
            raw_value = ""
        if field_type == "int":
            return int(raw_value)
        if field_type == "float":
            return float(raw_value)
        return raw_value.strip()

    def _field_definition(self, path):
        for field_path, label_key, field_type in CONFIG_FORM_FIELDS:
            if field_path == path:
                return label_key, field_type
        raise KeyError(path)

    def _select_options(self, path):
        if path == ('timezone',):
            return self._timezone_options()
        return SELECT_OPTIONS[path]

    def _timezone_options(self):
        global _TIMEZONE_OPTIONS
        if _TIMEZONE_OPTIONS is None:
            _TIMEZONE_OPTIONS = tuple(
                (timezone, timezone) for timezone in SUPPORTED_TIMEZONES)
        return _TIMEZONE_OPTIONS

    def _text(self, config, key):
        language = self._language(config)
        return self._text_for_language(language, key)

    def _text_for_language(self, language, key):
        language_text = TEXT[language] if language in TEXT else {}
        if key in language_text:
            return language_text[key]
        if key in TEXT["en"]:
            return TEXT["en"][key]
        raise KeyError("Missing web configuration text for key: {}".format(key))

    def _label(self, config, key):
        language = self._language(config)
        labels = TEXT.get(language, TEXT["en"])["labels"]
        return labels.get(key, TEXT["en"]["labels"][key])

    def _language(self, config):
        language = config.get("ui_lang", "en")
        if language not in SUPPORTED_LANGUAGES:
            language = language.split("_")[0].split("-")[0]
        if language not in TEXT:
            language = "en"
        return language

    def _set_no_store_headers(self):
        """Force fresh HTML so local users do not keep the old plain form cached."""
        response = getattr(cherrypy, "response", None)
        if response is not None:
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; "
                "frame-src https://www.openstreetmap.org; "
                "img-src 'self' data: https://*.tile.openstreetmap.org; "
                "connect-src 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'")
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"

    def _set_response_status(self, status):
        response = getattr(cherrypy, "response", None)
        if response is not None:
            response.status = status


def main():
    parser = ArgumentParser("Runs the local PiWeatherRock config UI")
    parser.add_argument('-c', '--config', required=True,
                        help='Path to your config file')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Host to bind to; defaults to localhost')
    parser.add_argument('--port', default=8888, type=int,
                        help='Port to bind to')
    parser.add_argument('--open', action='store_true',
                        help='Open the config UI in the default browser')
    args = parser.parse_args()

    config_file = os.path.abspath(args.config)
    available, port_error = _port_available(args.host, args.port)
    if not available:
        parser.exit(70, "Error: port {} is not available on {}: {}\n".format(
            args.port, args.host, port_error))

    cherrypy.config.update({
        'server.socket_host': args.host,
        'server.socket_port': args.port,
    })
    url = "http://{}:{}".format(_browser_host(args.host), args.port)
    print("PiWeatherRock config UI: {}".format(url))
    if args.open:
        webbrowser.open(url)
    cherrypy.quickstart(ConfigWebApp(config_file))


def _browser_host(host):
    if host in ("0.0.0.0", "::", ""):
        return "127.0.0.1"
    return host


def _port_available(host, port):
    family = socket.AF_INET6 if ":" in host and host != "0.0.0.0" else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError as exc:
            return False, exc
    return True, None


if __name__ == '__main__':
    main()
