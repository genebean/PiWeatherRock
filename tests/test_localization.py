import ast
import json
import os
import unittest

from piweatherrock.config_manager import ConfigError, SUPPORTED_LANGUAGES, validate_config
from piweatherrock.climate.openmeteo import get_weather_translations


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALIZATION_KEYS = {
    "check_at",
    "daylight",
    "feels_like",
    "humidity",
    "no_umbrella",
    "powered_by",
    "sunrise",
    "sunrise_at",
    "sunset",
    "sunset_at",
    "today",
    "tomorrow",
    "tonight",
    "umbrella",
    "wind",
}


def _valid_config(language):
    return {
        "ds_api_key": "openmeteo-request-piweatherrock",
        "lat": 40.299457,
        "lon": -3.743399,
        "units": "si",
        "lang": language,
        "ui_lang": language,
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
        },
        "log_level": "INFO",
    }


def _web_text():
    path = os.path.join(REPO_ROOT, "piweatherrock", "pwr_config_web.py")
    with open(path, "r", encoding="utf-8") as f:
        module = ast.parse(f.read())
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TEXT":
                    return ast.literal_eval(node.value)
    raise AssertionError("TEXT dictionary not found")


class LocalizationTest(unittest.TestCase):
    def test_required_languages_have_complete_ui_literals(self):
        data_dir = os.path.join(REPO_ROOT, "piweatherrock", "intl", "data")
        for language in SUPPORTED_LANGUAGES:
            path = os.path.join(data_dir, "piweatherrock.{}.json".format(language))
            with self.subTest(language=language):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual(set(data), {language})
                self.assertEqual(set(data[language]), LOCALIZATION_KEYS)

    def test_required_languages_are_valid_config_values(self):
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                self.assertTrue(validate_config(_valid_config(language)))

    def test_unsupported_languages_are_rejected(self):
        config = _valid_config("fr")
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_required_languages_have_weather_translations(self):
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                text = get_weather_translations(language, 0)
                self.assertNotIn(text, ("Unknown", "Desconocido"))
                self.assertNotEqual(text, "")

    def test_web_config_text_covers_required_languages(self):
        text = _web_text()
        en_keys = set(text["en"])
        en_label_keys = set(text["en"]["labels"])
        self.assertEqual(set(text), set(SUPPORTED_LANGUAGES))
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                self.assertEqual(set(text[language]), en_keys)
                self.assertEqual(set(text[language]["labels"]), en_label_keys)

    def test_package_data_includes_localization_files(self):
        path = os.path.join(REPO_ROOT, "pyproject.toml")
        with open(path, "r", encoding="utf-8") as f:
            self.assertIn('"intl/data/*.json"', f.read())


if __name__ == "__main__":
    unittest.main()
