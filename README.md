# PiWeatherRock

![GitHub](https://img.shields.io/github/license/genebean/PiWeatherRock)
![PyPI](https://img.shields.io/pypi/v/piweatherrock)

PiWeatherRock displays local weather on (almost) any screen you connect to a Raspberry Pi. It also works on other platforms, including macOS.

More information about the project and full documentation can be found at https://piweatherrock.technicalissues.us. Be sure to check out the getting started guide under the documentation link there for instruction on how to set everything up.

## Release process

- edit `version.py` according to the types of changes made
- edit `requirements.txt` if needed
- `python3 setup.py sdist bdist_wheel`
- `tar tzf dist/piweatherrock-*.tar.gz`
- `twine check dist/*`
- [optional] `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
- `twine upload dist/*`
- Create a git tag and push it
