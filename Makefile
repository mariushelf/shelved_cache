SHELL := /bin/bash

install:
	poetry install

clean:
	rm -rf dist

test: install
	poetry run tox -p -o -r

build:
	poetry build

publish: test clean build
	poetry run python -mtwine upload dist/* --verbose
