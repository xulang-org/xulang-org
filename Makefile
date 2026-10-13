XU_ROOT ?= $(abspath ../xu)
PYTHON ?= python3
BASE_PATH ?=
PORT ?= 8080
.DEFAULT_GOAL := build
.PHONY: build run run-http check api wasm
build:
	$(PYTHON) scripts/build-static.py --base-path "$(BASE_PATH)"
run:
	$(MAKE) build BASE_PATH=
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist
run-http:
	XU_ROOT="$(XU_ROOT)" ./scripts/run-local.sh
check:
	$(PYTHON) -m unittest discover -s tests -v
api:
	XU_ROOT="$(XU_ROOT)" XU_SRC="$(XU_ROOT)/src" ./scripts/gen-api
wasm:
	XU_SITE_ROOT="$(CURDIR)" "$(XU_ROOT)/scripts/build-xu-play-wasm.sh"
