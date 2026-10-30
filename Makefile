XU_ROOT ?= $(abspath ../xu)
XU_PACKAGES_ROOT ?= $(abspath ../packages)
XU_EXAMPLES_ROOT ?=
XU_EXAMPLES_REF ?=
PYTHON ?= python3
BASE_PATH ?=
PORT ?= 8080
.DEFAULT_GOAL := build
.PHONY: build run check check-playground check-chan api wasm clean
build:
	$(PYTHON) scripts/build-static.py --base-path "$(BASE_PATH)"
run:
	$(MAKE) build BASE_PATH=
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist
check:
	$(PYTHON) -m unittest discover -s tests -v
check-playground:
	$(PYTHON) scripts/sync-playground-design.py --check
	node --test tests/test_playground*.mjs
check-chan:
	$(PYTHON) tests/check_chan_examples.py --xu-root "$(XU_ROOT)"
api:
	$(PYTHON) scripts/gen-api.py --src "$(XU_ROOT)/src" --packages "$(XU_PACKAGES_ROOT)" $(if $(XU_EXAMPLES_ROOT),--examples "$(XU_EXAMPLES_ROOT)" --examples-ref "$(XU_EXAMPLES_REF)")
wasm:
	XU_ROOT="$(XU_ROOT)" ./scripts/build-playground.sh
clean:
	rm -rf -- build/playground dist
