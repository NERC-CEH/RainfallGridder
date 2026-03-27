# RainfallGridder

![PyPI version](https://img.shields.io/pypi/v/rainfall-gridder.svg)

Python package for interpolating rainfall data onto a regular grid.

* Codeberg: https://codeberg.org/thomasjkeel/RainfallGridder/
* PyPI package: https://pypi.org/project/RainfallGridder/
* Created by: **[Tom Keel](None)** | Codeberg https://codeberg.org/thomasjkeel | PyPI https://pypi.org/user/thomasjkeel/
* Free software: MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to Codeberg Pages.

[//]: # (* **Live site:** https://thomasjkeel.codeberg.io/RainfallGridder/)
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via Codeberg Actions. To enable this, go to your repo's Settings > Pages and set the source to **Codeberg Actions**.

## Development

To set up for local development:

```bash
# Clone your fork
git clone git@codeberg.org:your_username/RainfallGridder.git
cd RainfallGridder

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `rainfall_gridder`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

RainfallGridder was created in 2026 by Tom Keel.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
