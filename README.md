# PiWeatherRock

![GitHub](https://img.shields.io/github/license/genebean/PiWeatherRock)

Display local weather on a Raspberry Pi

Documentation lives at https://piweatherrock.technicalissues.us

## Release process

- edit `version.py` according to the types of changes made
- edit `requirements.txt` if needed
- `python3 setup.py sdist bdist_wheel`
- `tar tzf dist/piweatherrock-*.tar.gz`
- `twine check dist/*`
- [optional] `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
- `twine upload dist/*`
- Create a git tag and push it
