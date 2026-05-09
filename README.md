# PiWeatherRock

[![License: MIT](https://img.shields.io/github/license/carloshm/PiWeatherRock)](LICENSE)

PiWeatherRock displays local weather on (almost) any screen you connect to a Raspberry Pi. It also works on other platforms, including Windows and macOS.

## Weather API

This project uses the [Open-Meteo API](https://open-meteo.com/) to fetch weather data. Open-Meteo is a free, open-source weather API that does not require an API key for non-commercial use.

> **Note:** Previous versions of PiWeatherRock used the [Dark Sky API](https://darksky.net/), which was shut down. The project has been migrated to use Open-Meteo as a drop-in replacement. The internal data format still follows the Dark Sky structure for backward compatibility, with the `openmeteo.py` module handling the translation between APIs.

### Configuration

Weather settings are configured in `piweatherrock/piweatherrock-config.json`:

- `ds_api_key`: Identifier for the Open-Meteo request (no real API key needed). The name is a legacy reference from the Dark Sky era, kept for backward compatibility.
- `lat` / `lon`: Your location coordinates.
- `units`: Unit system (`si` for metric).
- `lang`: Language for weather descriptions (`en`, `es`, `ca`, `gl`, `eu`).
- `ui_lang`: Language for UI labels (`en`, `es`, `ca`, `gl`, `eu`).
- `timezone`: Your timezone (e.g., `Europe/Madrid`).
- `update_freq`: How often to refresh weather data (in seconds).
- `fullscreen`, `12hour_disp`, `icon_offset`: Display behavior.
- `info_pause`, `info_delay`, `plugins`: Page rotation behavior. `plugins`
  controls which screens are shown (`daily`, `hourly`, `info`, `media`) and
  each screen's display time.
- `plugins.media`: Local media screen settings for images and short videos
  loaded from a folder. Configure `enabled`, `pause`, `path`, `shuffle`, `fit`
  (`contain`, `cover`, or `stretch`), and allowed `extensions`.
  The folder in `path` must already exist before enabling this screen.

PiWeatherRock automatically checks the config file while `pwr-ui` is running.
Valid changes are applied without restarting the display. If the JSON is invalid,
the active configuration remains in use and the error is logged.

You can edit the same JSON from the local web configuration UI:

```bash
pwr-config-web -c ./piweatherrock/piweatherrock-config.json
```

The config UI binds to `127.0.0.1:8888` by default. Use `--host` and `--port`
only when you intentionally want to expose it elsewhere on your network.
Add `--open` to launch the default browser automatically. If the chosen port is
already in use, the command exits with a clear error instead of a server stack
trace.
The same UI exposes the screen selection, display time, and local media folder
settings. The location map can be panned and zoomed normally; use the pin button
when you want a map click to update latitude and longitude. The interface
supports both light and dark themes with an automatic toggle based on system
preference. It also includes runtime validation, CSRF-protected saves, security
headers, and an Open-Meteo test using the configured latitude, longitude, and
timezone.
See the expanded visual guide in [`docs/README.md`](docs/README.md#aplicaci%C3%B3n-web-de-configuraci%C3%B3n).

## Installation

PiWeatherRock is packaged with `pyproject.toml` and installs the current
console commands `pwr-ui`, `pwr-config-web`, and `pwr-config-upgrade`.

### Raspberry Pi / Linux

Use the installation script from the repository root:

```bash
git clone https://github.com/carloshm/PiWeatherRock.git
cd PiWeatherRock
chmod +x install.sh
./install.sh Europe/Madrid
```

The optional argument is the system timezone. The script installs the required
system packages, creates a virtual environment at `~/pwr-env`, installs
PiWeatherRock with `pip install .`, and prints the commands needed to run the
application.

Before starting the UI, create and edit your configuration file. The sample
configuration defaults to Getafe, Spain (`Europe/Madrid`):

```bash
source ~/pwr-env/bin/activate
cp piweatherrock/config.json-sample piweatherrock/piweatherrock-config.json
# Edit piweatherrock/piweatherrock-config.json with your coordinates, timezone, language, and display options.
pwr-ui -c ./piweatherrock/piweatherrock-config.json
```

### Manual or development installation (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install .
cp piweatherrock/config.json-sample piweatherrock/piweatherrock-config.json
# Edit piweatherrock/piweatherrock-config.json before running.
pwr-ui -c ./piweatherrock/piweatherrock-config.json
```

### Manual or development installation (Windows)

Use PowerShell from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip setuptools wheel
py -m pip install .
Copy-Item piweatherrock\config.json-sample piweatherrock\piweatherrock-config.json
# Edit piweatherrock\piweatherrock-config.json before running.
pwr-ui -c .\piweatherrock\piweatherrock-config.json
```

The `pwr-config-web` configuration UI works the same way on Windows, macOS,
and Linux. Local image playback uses pygame on all supported platforms. Local
video playback requires `ffmpeg` to be installed and available on `PATH`. Local
media paths may use `~` or environment variables, but the expanded folder must
exist before enabling the media page.

If your shell reports `pwr-config-web: command not found`, the PiWeatherRock
package is not installed in the currently active virtual environment. From the
repository root, activate the environment and reinstall the package:

```bash
source ~/pwr-env/bin/activate
python3 -m pip install .
```

Then verify that `pwr-config-web` is on `PATH` with `command -v pwr-config-web`.

See [`docs/`](docs/) for an application walkthrough with screenshots.

## Release process

- Update version in `pyproject.toml` according to the types of changes made
- Update `requirements.txt` if needed
- `python3 -m pip install --upgrade build twine`
- `python3 -m build`
- `tar tzf dist/piweatherrock-*.tar.gz`
- `twine check dist/*`
- [optional] `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
- `twine upload dist/*`
- Create a git tag and push it

## Local Development process

```bash
python3 -m venv env_name
source env_name/bin/activate
```

```bash
git clone https://github.com/carloshm/PiWeatherRock.git
cd PiWeatherRock
git pull  # for any additional external change after a while
```

Make changes

```bash
git add .
git commit -m "changes description"
git push origin main
```

## Run changes

After making code changes in a local checkout, reinstall the package in your
active virtual environment and run the UI with your configuration file:

```bash
python3 -m pip install .
pwr-ui -c ./piweatherrock/piweatherrock-config.json
```

To configure from a browser:

```bash
pwr-config-web -c ./piweatherrock/piweatherrock-config.json
```

> **Note:** `pwr-ui`, `pwr-config-web`, and `pwr-config-upgrade` are installed as console entry points via `pyproject.toml`. See [PEP 621](https://peps.python.org/pep-0621/) and [setup.py deprecation](https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html) for background.

## Validate Service Data

You can test the Open-Meteo API directly with a request like this:

```
https://api.open-meteo.com/v1/forecast?latitude=40.299457&longitude=-3.743399&timezone=Europe/Madrid&models=best_match&forecast_days=4&current_weather=true&temperature_unit=celsius&windspeed_unit=kmh&precipitation_unit=mm&timeformat=iso8601&hourly=visibility,weathercode,temperature_2m,relativehumidity_2m,apparent_temperature,surface_pressure,cloudcover,windspeed_80m,precipitation,precipitation_probability,dewpoint_2m,windspeed_10m,windgusts_10m,winddirection_10m,cloudcover_low,direct_radiation&daily=sunrise,sunset,uv_index_max,weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_mean,precipitation_probability_min,windgusts_10m_max,precipitation_probability_max,windspeed_10m_max,winddirection_10m_dominant
```

For more details on available parameters, see the [Open-Meteo API documentation](https://open-meteo.com/en/docs).
