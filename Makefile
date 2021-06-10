SHELL := /bin/bash

install:
	poetry update

clean:
	rm -rf dist

test: install
	poetry run tox -p -o -r

build:
	poetry build

publish: test clean build
	poetry run python -mtwine upload dist/* --verbose
