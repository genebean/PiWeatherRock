# Change log

## [3.0.0](https://github.com/carloshm/PiWeatherRock) - 2026-05-08

- Migrated weather API from Dark Sky to [Open-Meteo](https://open-meteo.com/)
- Added `openmeteo.py` module to translate Open-Meteo responses to the internal Dark Sky data format
- No API key is required for non-commercial use with Open-Meteo
- Added internationalization support with `intl` module
- Updated configuration to use Open-Meteo endpoint
- Migrated packaging from `setup.py` to `pyproject.toml` (PEP 621)
- Added `timezone` to configuration
- Updated project metadata and homepage to carloshm fork
- Added current console entry points: `pwr-ui`, `pwr-config-web`, and `pwr-config-upgrade`
- Added a guided local web configuration UI with map-based location selection, theme support, runtime validation, and Open-Meteo test
- Added hot-reload support so valid JSON configuration changes can be applied while `pwr-ui` is running
- Added local media screen support for images and short videos, including fit modes and `ffmpeg`-based video playback
- Improved cross-platform support for Windows, macOS, and Linux display initialization
- Made video frame reading compatible with Windows by replacing pipe `select()` usage with a background reader queue
- Added safer config web handling with CSRF-protected saves, fixed success messages, and security headers
- Added UTF-8 config reading/writing and `~`/environment variable expansion for local media paths
- Updated the default sample/runtime configuration for Getafe (`Europe/Madrid`) and `cover` media fit
- Updated installation and usage documentation, including Windows PowerShell instructions and the corrected MIT license link

## [2.1.0](https://github.com/genebean/PiWeatherRock/tree/2.1.0)

- Add option for 24h time

## [2.0.1](https://github.com/genebean/PiWeatherRock/tree/2.0.1)

- Update url in `setup.py` to the documentation site
- Update this changelog (I forgot before releasing 2.0.0)
- Update the readme a little.

## [2.0.0](https://github.com/genebean/PiWeatherRock/tree/2.0.0)

- Add this change log
- Update code for Python 3 compatibility
- Move to using a central license file instead of adding the full MIT license
  to each file.
- Moved logging from syslog to a local file and made it visible via the config
  page
- sync'ed versions between GitHub and the code here
- Migrated from a monorepo to multiple python packages and modules
- Migrated puppet code to
  [https://forge.puppet.com/genebean/piweatherrock](https://forge.puppet.com/genebean/piweatherrock)

## [1.3.0](https://github.com/genebean/PiWeatherRock/tree/1.3.0)

- Added web-based configuration (thanks @mettaMMA)
  This also caused the configuration to move from a Python file to JSON.

## [1.2.1](https://github.com/genebean/PiWeatherRock/tree/1.2.1)

- Fixed bug impacting switching screens with the keyboard

## [1.2.0](https://github.com/genebean/PiWeatherRock/tree/1.2.0)

- Mostly code cleanup plus added the ability to adjust screen timing

## [1.1.0](https://github.com/genebean/PiWeatherRock/tree/1.1.0)

- Added language setting for calls to Dark Sky's API

## [1.0.0](https://github.com/genebean/PiWeatherRock/tree/1.0.0)

- First stable release that includes proper documentation.
  The documentation now lives at https://piweatherrock.technicalissues.us
