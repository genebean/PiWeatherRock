# -*- coding: utf-8 -*-
"""Configuration loading, validation, and hot-reload helpers."""

import copy
import json
import os
import shutil
import tempfile
import time

from pytz import common_timezones


class ConfigError(Exception):
    """Raised when a configuration file cannot be loaded or validated."""


REQUIRED_FIELDS = {
    "ds_api_key": str,
    "lat": (int, float),
    "lon": (int, float),
    "units": str,
    "lang": str,
    "ui_lang": str,
    "timezone": str,
    "fullscreen": bool,
    "12hour_disp": bool,
    "icon_offset": (int, float),
    "update_freq": int,
    "info_pause": int,
    "info_delay": int,
    "plugins": dict,
    "log_level": str,
}

PLUGIN_FIELDS = {
    "enabled": bool,
    "pause": int,
}

DEFAULT_PLUGINS = {
    "daily": {
        "enabled": True,
        "pause": 60,
    },
    "hourly": {
        "enabled": True,
        "pause": 60,
    },
    "info": {
        "enabled": True,
        "pause": 300,
    },
    "media": {
        "enabled": False,
        "pause": 20,
        "path": "",
        "shuffle": False,
        "fit": "cover",
        "extensions": "jpg,jpeg,png,gif,bmp,mp4,mov,m4v,avi,webm",
    },
}

MEDIA_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "bmp")
MEDIA_VIDEO_EXTENSIONS = ("mp4", "mov", "m4v", "avi", "webm")
MEDIA_FIT_MODES = ("contain", "cover", "stretch")

SUPPORTED_LANGUAGES = ("en", "es", "ca", "gl", "eu")
SUPPORTED_TIMEZONES = tuple(common_timezones)

WEATHER_RELOAD_PATHS = {
    ("ds_api_key",),
    ("lat",),
    ("lon",),
    ("units",),
    ("lang",),
    ("timezone",),
    ("update_freq",),
}

DISPLAY_RELOAD_PATHS = {
    ("fullscreen",),
}

SUN_TIME_RELOAD_PATHS = {
    ("12hour_disp",),
    ("ui_lang",),
}

LOG_RELOAD_PATHS = {
    ("log_level",),
}

ROTATION_RELOAD_PATHS = {
    ("info_pause",),
    ("info_delay",),
    ("plugins",),
}


CONFIG_FORM_FIELDS = [
    (("lat",), "lat", "float"),
    (("lon",), "lon", "float"),
    (("timezone",), "timezone", "text"),
    (("ds_api_key",), "ds_api_key", "text"),
    (("units",), "units", "text"),
    (("lang",), "lang", "text"),
    (("ui_lang",), "ui_lang", "text"),
    (("update_freq",), "update_freq", "int"),
    (("fullscreen",), "fullscreen", "bool"),
    (("12hour_disp",), "12hour_disp", "bool"),
    (("icon_offset",), "icon_offset", "float"),
    (("info_pause",), "info_pause", "int"),
    (("info_delay",), "info_delay", "int"),
    (("plugins", "daily", "enabled"), "daily_enabled", "bool"),
    (("plugins", "daily", "pause"), "daily_pause", "int"),
    (("plugins", "hourly", "enabled"), "hourly_enabled", "bool"),
    (("plugins", "hourly", "pause"), "hourly_pause", "int"),
    (("plugins", "info", "enabled"), "info_enabled", "bool"),
    (("plugins", "info", "pause"), "info_pause_plugin", "int"),
    (("plugins", "media", "enabled"), "media_enabled", "bool"),
    (("plugins", "media", "pause"), "media_pause", "int"),
    (("plugins", "media", "path"), "media_path", "text"),
    (("plugins", "media", "shuffle"), "media_shuffle", "bool"),
    (("plugins", "media", "fit"), "media_fit", "text"),
    (("plugins", "media", "extensions"), "media_extensions", "text"),
    (("log_level",), "log_level", "text"),
]


def load_config(config_file):
    """Load and validate a PiWeatherRock JSON configuration."""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (IOError, ValueError) as exc:
        raise ConfigError("Could not load config file '{}': {}".format(
            config_file, exc))

    normalized = normalize_config(config)
    validate_config(normalized)
    return normalized


def validate_config(config):
    """Validate required fields and value ranges."""
    errors = []

    if not isinstance(config, dict):
        raise ConfigError("Config must be a JSON object")

    for key, expected_type in REQUIRED_FIELDS.items():
        if key not in config:
            errors.append("Missing required field '{}'".format(key))
        elif not _is_expected_type(config[key], expected_type):
            errors.append("Field '{}' has invalid type".format(key))

    plugins = config.get("plugins")
    if isinstance(plugins, dict):
        normalized_plugins = merge_defaults(plugins, DEFAULT_PLUGINS)
        for plugin_name in DEFAULT_PLUGINS:
            plugin_config = normalized_plugins.get(plugin_name)
            if not isinstance(plugin_config, dict):
                errors.append("Missing plugin '{}' configuration".format(plugin_name))
                continue
            for key, expected_type in PLUGIN_FIELDS.items():
                if key not in plugin_config:
                    errors.append("Missing plugins.{}.{}".format(plugin_name, key))
                elif not _is_expected_type(plugin_config[key], expected_type):
                    errors.append("Field plugins.{}.{} has invalid type".format(
                        plugin_name, key))
            if plugin_name == "media":
                _validate_media_plugin(plugin_config, errors)

    _validate_range(config, "lat", -90, 90, errors)
    _validate_range(config, "lon", -180, 180, errors)
    _validate_positive_int(config, "update_freq", errors)
    _validate_positive_int(config, "info_pause", errors)
    _validate_positive_int(config, "info_delay", errors)
    _validate_language(config, "lang", errors)
    _validate_language(config, "ui_lang", errors)
    _validate_timezone(config, errors)

    if isinstance(plugins, dict):
        enabled_count = 0
        normalized_plugins = merge_defaults(plugins, DEFAULT_PLUGINS)
        for plugin_name in DEFAULT_PLUGINS:
            plugin_config = normalized_plugins.get(plugin_name)
            if isinstance(plugin_config, dict):
                _validate_positive_int(plugin_config, "pause", errors,
                                       "plugins.{}.pause".format(plugin_name))
                if plugin_config.get("enabled") is True:
                    enabled_count += 1
        if enabled_count == 0:
            errors.append("At least one plugin must be enabled")

    if errors:
        raise ConfigError("Invalid configuration: " + "; ".join(errors))

    return True


def normalize_config(config):
    """Return a copy of config with current plugin defaults filled in."""
    normalized = copy.deepcopy(config)
    normalized["plugins"] = merge_defaults(
        normalized.get("plugins", {}), DEFAULT_PLUGINS)
    return normalized


def merge_defaults(config, default_config):
    """Return a copy of config with missing keys filled from default_config."""
    merged = copy.deepcopy(config)
    for key, value in default_config.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
        elif isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_defaults(merged[key], value)
    return merged


def write_config_atomic(config_file, config, backup=True):
    """Validate and write config atomically, preserving the previous file."""
    config = normalize_config(config)
    validate_config(config)

    config_dir = os.path.dirname(os.path.abspath(config_file)) or "."
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    if backup and os.path.exists(config_file):
        shutil.copy2(config_file, config_file + ".bak")

    fd, temp_file = tempfile.mkstemp(
        prefix=".{}.".format(os.path.basename(config_file)),
        suffix=".tmp",
        dir=config_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, sort_keys=True)
            f.write("\n")
        os.replace(temp_file, config_file)
    except Exception:
        try:
            os.remove(temp_file)
        except OSError:
            pass
        raise


def diff_config(old_config, new_config):
    """Return leaf paths whose values changed between two config dicts."""
    changed = set()
    _collect_diff((), old_config, new_config, changed)
    return changed


def config_changed(changed_paths, interesting_paths):
    """Return True if any changed path affects one of the interesting paths."""
    for changed_path in changed_paths:
        for interesting_path in interesting_paths:
            if _path_related(changed_path, interesting_path):
                return True
    return False


def get_config_value(config, path):
    value = config
    for part in path:
        value = value[part]
    return value


def set_config_value(config, path, value):
    target = config
    for part in path[:-1]:
        target = target.setdefault(part, {})
    target[path[-1]] = value


def field_name(path):
    return "__".join(path)


class ConfigWatcher:
    """Polls a config file and reports validated changes."""

    def __init__(self, config_file, interval=1.0):
        self.config_file = config_file
        self.interval = interval
        self.last_check = 0
        self.last_signature = file_signature(config_file)

    def changed_config(self):
        now = time.time()
        if now - self.last_check < self.interval:
            return None
        self.last_check = now

        signature = file_signature(self.config_file)
        if signature == self.last_signature:
            return None

        config = load_config(self.config_file)
        return signature, config

    def commit(self, signature):
        self.last_signature = signature

    def sync_signature(self):
        self.last_signature = file_signature(self.config_file)


def file_signature(config_file):
    stat = os.stat(config_file)
    mtime = getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1e9))
    return mtime, stat.st_size


def _is_expected_type(value, expected_type):
    if expected_type is bool:
        return isinstance(value, bool)
    if expected_type in (int, (int, float)):
        return isinstance(value, expected_type) and not isinstance(value, bool)
    return isinstance(value, expected_type)


def _validate_range(config, key, minimum, maximum, errors):
    value = config.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < minimum or value > maximum:
            errors.append("Field '{}' must be between {} and {}".format(
                key, minimum, maximum))


def _validate_positive_int(config, key, errors, display_name=None):
    value = config.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value <= 0:
        errors.append("Field '{}' must be greater than 0".format(
            display_name or key))


def _validate_language(config, key, errors):
    value = config.get(key)
    if isinstance(value, str) and value not in SUPPORTED_LANGUAGES:
        errors.append("Field '{}' must be one of: {}".format(
            key, ", ".join(SUPPORTED_LANGUAGES)))


def _validate_timezone(config, errors):
    value = config.get("timezone")
    if isinstance(value, str) and value not in SUPPORTED_TIMEZONES:
        errors.append("Field 'timezone' must be a valid timezone")


def _validate_media_plugin(plugin_config, errors):
    if not isinstance(plugin_config.get("path"), str):
        errors.append("Field plugins.media.path has invalid type")
    elif plugin_config.get("enabled") and not plugin_config["path"]:
        errors.append("Field plugins.media.path is required when media is enabled")
    elif (plugin_config.get("enabled")
          and not os.path.isdir(expand_config_path(plugin_config["path"]))):
        errors.append("Field plugins.media.path must be an existing directory")
    if not isinstance(plugin_config.get("shuffle"), bool):
        errors.append("Field plugins.media.shuffle has invalid type")
    if not isinstance(plugin_config.get("fit"), str):
        errors.append("Field plugins.media.fit has invalid type")
    elif plugin_config["fit"] not in MEDIA_FIT_MODES:
        errors.append("Field plugins.media.fit must be one of: {}".format(
            ", ".join(MEDIA_FIT_MODES)))
    if not isinstance(plugin_config.get("extensions"), str):
        errors.append("Field plugins.media.extensions has invalid type")
        return
    configured = plugin_config["extensions"]
    allowed = set(MEDIA_IMAGE_EXTENSIONS + MEDIA_VIDEO_EXTENSIONS)
    for extension in _split_extensions(configured):
        if extension not in allowed:
            errors.append("Unsupported media extension '{}'".format(extension))


def _split_extensions(value):
    extensions = []
    for part in value.split(","):
        extension = part.strip().lower().lstrip(".")
        if extension:
            extensions.append(extension)
    return extensions


def expand_config_path(path):
    """Expand user and environment variables in configured local paths."""
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def _collect_diff(path, old_value, new_value, changed):
    if isinstance(old_value, dict) and isinstance(new_value, dict):
        keys = set(old_value.keys()) | set(new_value.keys())
        for key in keys:
            _collect_diff(path + (key,), old_value.get(key), new_value.get(key),
                          changed)
    elif old_value != new_value:
        changed.add(path)


def _path_related(changed_path, interesting_path):
    shortest = min(len(changed_path), len(interesting_path))
    return changed_path[:shortest] == interesting_path[:shortest]
