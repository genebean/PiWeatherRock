import importlib
from pathlib import Path
import types
import unittest
from unittest import mock


def _config_web_module():
    try:
        import cherrypy  # noqa: F401
    except ImportError:
        cherrypy = types.ModuleType("cherrypy")
        cherrypy.expose = lambda function: function
        with mock.patch.dict("sys.modules", {"cherrypy": cherrypy}):
            module = importlib.import_module("piweatherrock.pwr_config_web")
    else:
        module = importlib.import_module("piweatherrock.pwr_config_web")
    return module


ConfigWebModule = _config_web_module()
ConfigWebApp = ConfigWebModule.ConfigWebApp


VALID_CONFIG = {
    "ds_api_key": "openmeteo-request-piweatherrock",
    "lat": 40.299457,
    "lon": -3.743399,
    "units": "si",
    "lang": "es",
    "ui_lang": "es",
    "timezone": "Europe/Madrid",
    "fullscreen": True,
    "12hour_disp": False,
    "icon_offset": -23.5,
    "update_freq": 900,
    "info_pause": 60,
    "info_delay": 900,
    "plugins": {
        "daily": {"pause": 60, "enabled": True},
        "hourly": {"pause": 60, "enabled": True},
        "info": {"pause": 300, "enabled": True},
        "media": {
            "pause": 20,
            "enabled": False,
            "path": "",
            "shuffle": False,
            "fit": "contain",
            "extensions": "jpg,jpeg,png,gif,bmp,mp4,mov,m4v,avi,webm",
        },
    },
    "log_level": "INFO",
}


class ConfigWebTest(unittest.TestCase):
    def test_current_entrypoint_in_pyproject(self):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        text = pyproject.read_text()

        self.assertIn('pwr-config-web = "piweatherrock.pwr_config_web:main"', text)
        self.assertNotIn("pwr-webconfig", text)
        self.assertNotIn("piweatherrock-webconfig", text)

    def test_form_groups_fields_with_help_and_map(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('<section class="card" aria-labelledby="location-title">', html)
        self.assertIn('class="help-icon" tabindex="0" role="button"', html)
        self.assertIn('<header class="hero">', html)
        self.assertIn('id="location-map"', html)
        self.assertIn('id="map-picker"', html)
        self.assertIn('id="map-pick-toggle"', html)
        self.assertIn('class="location-layout"', html)
        self.assertIn('id="location-preset"', html)
        self.assertIn('openstreetmap.org/export/embed.html', html)
        self.assertIn('pointer-events: none', html)
        self.assertIn('.map-panel.picking .map-picker', html)
        self.assertIn("picker.addEventListener('click'", html)
        self.assertNotIn("<fieldset", html)
        self.assertNotIn("<legend", html)

    def test_form_uses_selects_for_constrained_values(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('<select id="timezone" name="timezone">', html)
        self.assertIn('<option value="Europe/Madrid" selected>Europe/Madrid</option>', html)
        self.assertIn('<select id="lang" name="lang">', html)
        self.assertIn('<select id="plugins__media__fit" name="plugins__media__fit">', html)

    def test_pause_labels_group_global_and_per_page_pauses(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)
        english_config = dict(VALID_CONFIG, ui_lang="en")
        english_html = ConfigWebApp("config.json")._render_form(english_config)

        self.assertIn('Controles globales', html)
        self.assertIn('Visibilidad por página', html)
        self.assertIn('Duración visible de página diaria', html)
        self.assertIn('Duración visible de página de medios locales', html)
        self.assertIn('Global controls', english_html)
        self.assertIn('Per-page visibility', english_html)
        self.assertLess(
            html.index('Pausa global del ciclo de información'),
            html.index('Duración visible de página diaria'))

    def test_page_includes_theme_toggle(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('id="theme-toggle"', html)
        self.assertIn('data-theme', html)
        self.assertIn('localStorage', html)

    def test_location_section_includes_preset_selector(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('id="location-preset"', html)
        self.assertIn('<option value="40.30825,-3.732393">Getafe</option>', html)
        self.assertIn('<option value="40.416775,-3.70379">Madrid</option>', html)
        self.assertIn("preset.addEventListener('change'", html)
        self.assertIn("pickToggle.addEventListener('click'", html)

    def test_media_section_rendered(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('aria-labelledby="media-title"', html)
        self.assertIn('plugins__media__enabled', html)
        self.assertIn('plugins__media__path', html)
        self.assertIn('plugins__media__fit', html)
        self.assertIn('class="field-grid media-grid"', html)
        self.assertIn('Usa una carpeta que exista', html)
        self.assertIn('variables de entorno se expanden', html)

    def test_help_icon_uses_large_custom_tooltip(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('data-tooltip=', html)
        self.assertIn('<span aria-hidden="true">?</span>', html)
        self.assertNotIn('&#9757;', html)

    def test_form_links_to_validation_and_weather_test(self):
        html = ConfigWebApp("config.json")._render_form(VALID_CONFIG)

        self.assertIn('href="/validate"', html)
        self.assertIn('href="/test_weather"', html)
        self.assertIn('Probar Open-Meteo', html)

    def test_form_uses_csrf_token_and_fixed_saved_message(self):
        app = ConfigWebApp("config.json")
        html = app._render_form(VALID_CONFIG)

        self.assertIn('name="csrf_token"', html)
        request = types.SimpleNamespace(method="POST")
        with mock.patch.object(
                ConfigWebModule.cherrypy, "request", request, create=True):
            self.assertTrue(app._valid_save_request(
                VALID_CONFIG, {"csrf_token": app.csrf_token}))
            self.assertFalse(app._valid_save_request(
                VALID_CONFIG, {"csrf_token": "wrong"}))
            request.method = "GET"
            self.assertFalse(app._valid_save_request(
                VALID_CONFIG, {"csrf_token": app.csrf_token}))
        self.assertNotIn("message=", html)


if __name__ == "__main__":
    unittest.main()
