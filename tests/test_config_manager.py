import json
import os
import tempfile
import unittest

from piweatherrock.config_manager import (
    ConfigError,
    ConfigWatcher,
    diff_config,
    load_config,
    merge_defaults,
    normalize_config,
    validate_config,
    write_config_atomic,
)


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


class ConfigManagerTest(unittest.TestCase):
    def test_load_config_rejects_invalid_json(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("{")
            path = f.name
        try:
            with self.assertRaises(ConfigError):
                load_config(path)
        finally:
            os.remove(path)

    def test_load_config_reads_utf8_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            media_dir = os.path.join(tmpdir, "Imágenes")
            os.mkdir(media_dir)
            path = os.path.join(tmpdir, "config.json")
            config = dict(VALID_CONFIG)
            config["plugins"] = dict(VALID_CONFIG["plugins"])
            config["plugins"]["media"] = dict(VALID_CONFIG["plugins"]["media"])
            config["plugins"]["media"]["enabled"] = True
            config["plugins"]["media"]["path"] = media_dir
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f)

            loaded = load_config(path)

            self.assertEqual(loaded["plugins"]["media"]["path"], media_dir)

    def test_sample_config_defaults_to_getafe(self):
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "piweatherrock",
            "config.json-sample")
        config = load_config(sample_path)

        self.assertEqual(config["timezone"], "Europe/Madrid")
        self.assertAlmostEqual(config["lat"], 40.30825)
        self.assertAlmostEqual(config["lon"], -3.732393)
        self.assertEqual(config["plugins"]["media"]["fit"], "cover")

    def test_media_path_validation_expands_environment_variables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_value = os.environ.get("PWR_TEST_MEDIA_DIR")
            os.environ["PWR_TEST_MEDIA_DIR"] = tmpdir
            try:
                config = dict(VALID_CONFIG)
                config["plugins"] = dict(VALID_CONFIG["plugins"])
                config["plugins"]["media"] = dict(
                    VALID_CONFIG["plugins"]["media"])
                config["plugins"]["media"]["enabled"] = True
                config["plugins"]["media"]["path"] = (
                    "%PWR_TEST_MEDIA_DIR%"
                    if os.name == "nt" else "$PWR_TEST_MEDIA_DIR")

                self.assertTrue(validate_config(config))
            finally:
                if old_value is None:
                    os.environ.pop("PWR_TEST_MEDIA_DIR", None)
                else:
                    os.environ["PWR_TEST_MEDIA_DIR"] = old_value

    def test_write_config_atomic_creates_backup_and_valid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            write_config_atomic(path, VALID_CONFIG, backup=False)
            updated = dict(VALID_CONFIG)
            updated["lat"] = 1.25
            write_config_atomic(path, updated)

            self.assertTrue(os.path.exists(path + ".bak"))
            self.assertEqual(load_config(path)["lat"], 1.25)
            self.assertEqual(load_config(path + ".bak")["lat"], VALID_CONFIG["lat"])

    def test_write_config_atomic_rejects_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            invalid = dict(VALID_CONFIG)
            invalid["lat"] = 91
            with self.assertRaises(ConfigError):
                write_config_atomic(path, invalid, backup=False)
            self.assertFalse(os.path.exists(path))

    def test_diff_config_reports_nested_changes(self):
        updated = json.loads(json.dumps(VALID_CONFIG))
        updated["plugins"]["daily"]["pause"] = 30
        self.assertEqual(
            diff_config(VALID_CONFIG, updated),
            {("plugins", "daily", "pause")})

    def test_merge_defaults_adds_nested_missing_keys(self):
        partial = {"plugins": {"daily": {"pause": 30}}}
        defaults = {"plugins": {"daily": {"enabled": True}, "hourly": {"pause": 60}}}
        merged = merge_defaults(partial, defaults)
        self.assertTrue(merged["plugins"]["daily"]["enabled"])
        self.assertEqual(merged["plugins"]["hourly"]["pause"], 60)

    def test_normalize_config_adds_media_and_info_defaults(self):
        partial = json.loads(json.dumps(VALID_CONFIG))
        del partial["plugins"]["info"]
        del partial["plugins"]["media"]
        normalized = normalize_config(partial)
        self.assertTrue(normalized["plugins"]["info"]["enabled"])
        self.assertFalse(normalized["plugins"]["media"]["enabled"])

    def test_validate_config_rejects_no_enabled_pages(self):
        config = json.loads(json.dumps(VALID_CONFIG))
        for plugin in config["plugins"].values():
            plugin["enabled"] = False
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_validate_config_requires_media_path_when_enabled(self):
        config = json.loads(json.dumps(VALID_CONFIG))
        config["plugins"]["media"]["enabled"] = True
        config["plugins"]["media"]["path"] = ""
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_validate_config_rejects_unknown_timezone(self):
        config = json.loads(json.dumps(VALID_CONFIG))
        config["timezone"] = "Europe/Unknown"
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_config_watcher_detects_file_replacement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            write_config_atomic(path, VALID_CONFIG, backup=False)
            watcher = ConfigWatcher(path, interval=0)
            updated = dict(VALID_CONFIG)
            updated["update_freq"] = 300
            write_config_atomic(path, updated, backup=False)
            result = watcher.changed_config()
            self.assertIsNotNone(result)
            signature, config = result
            self.assertEqual(config["update_freq"], 300)
            watcher.commit(signature)
            self.assertIsNone(watcher.changed_config())


if __name__ == "__main__":
    unittest.main()
