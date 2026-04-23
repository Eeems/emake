[project]
name = "{name}"
version = "0.0.1"
description = "{description}"
requires-python = ">={python_version}"
license = "{license_spdx}"
authors = [{{name = "{author_name}", email = "{author_email}"}}]
classifiers = [
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
]

[build-system]
requires = ["setuptools>=70.1", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = [
    "pytest",
]

[tool.setuptools]
packages = ["{name}"]

[tool.ruff]
exclude = [".venv", "build"]

[tool.ruff.lint]
extend-select = [
    "UP",
    "PL",
    "ANN",
    "S",
]
ignore = [
    "PLW0603",
    "PLR2004",
    "PLR0915",
    "PLR0912",
    "PLR0911",
    "PLR6301",
    "PLR0913",
    "S101",
    "S404",
    "S603",
    "S607",
    "ANN401",
    "ANN001",
    "ANN003",
]

[tool.pyright]
exclude = [".venv", "build"]
