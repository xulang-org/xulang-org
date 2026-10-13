XU_ROOT ?= $(abspath ../xu)
XU_PACKAGES_ROOT ?= $(abspath ../packages)
PYTHON ?= python3
BASE_PATH ?=
PORT ?= 8080
.DEFAULT_GOAL := build
.PHONY: build run run-http check check-playground check-chan api wasm
build:
	$(PYTHON) scripts/build-static.py --base-path "$(BASE_PATH)"
run:
	$(MAKE) build BASE_PATH=
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist
run-http:
	XU_ROOT="$(XU_ROOT)" ./scripts/run-local.sh
check:
	$(PYTHON) -m unittest discover -s tests -v
check-playground:
	node --test tests/test_playground*.mjs
check-chan:
	$(PYTHON) tests/check_chan_examples.py --xu-root "$(XU_ROOT)"
api:
	XU_ROOT="$(XU_ROOT)" XU_SRC="$(XU_ROOT)/src" XU_PACKAGES_ROOT="$(XU_PACKAGES_ROOT)" ./scripts/gen-api
wasm:
	./scripts/build-playground.sh
