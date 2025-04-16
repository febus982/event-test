# Event test

This is an example implementation of a python application ingesting events and returning alerts
on specific scenarios.

It is built using https://github.com/febus982/bootstrap-python-fastapi, to setup some standard
setup for logging and observability.

## Documentation

The detailed documentation is available:

* Offline by running `make docs` after installing dependencies with `make dev-dependencies` (this can be expanded as needed and deployed on github pages)

## How to run

This application can be ran using `make` and either `uv` or `Docker`:

- `make` should be installed by default on MacOS or linux
- You can install `uv` on Mac using `brew`: `brew install uv` (refer to official installation)
- Download and install Docker: https://www.docker.com/products/docker-desktop/

Using Docker:

* `make containers`: Build containers
* `docker compose up dev-http`: Run HTTP application with hot reload
* `docker compose run --rm test`: Run test suite

Using Make and UV (you still need Docker for most of them):

* `make dev-dependencies`: Install dev requirements
* `make dev-http`: Run HTTP application with hot reload
* `make test`: Run unit test suite
* `make check`: Run all checks (tests, code style and lint)

## Other commands for development

* `make fix`: Run tests, code style and lint checks with automatic fixes (where possible)
