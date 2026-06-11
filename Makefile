.PHONY: install test map produce clean

# Defaults for `make produce`
W ?= 15
H ?= 15
P ?= 10
OUTPUT_DIR ?= output/database

install:
	pip install -e .

test:
	cd tests && python -m unittest discover -p 'test_*.py' -v

map:
	hashi calibrate

produce:
	hashi produce $(W) $(H) $(P) -d $(OUTPUT_DIR)

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -type d -exec rm -rf {} +
