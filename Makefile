PY := python3
FLAGS := -b
SRC_DIR := hashi
TESTS_DIR := tests
PUZZLES_DIR := puzzles

TEST_PUZZLE = $(PUZZLES_DIR)/puzzle_3.csv

REQUIREMENTS_FILE := requirements.txt

GENERATOR_SCRIPT := $(SRC_DIR)/generator.py
SOLVER_SCRIPT := $(SRC_DIR)/solver.py
VISUALISER_SCRIPT := $(SRC_DIR)/visualiser.py

TEST_SCRIPT := $(TESTS_DIR)/hashi_test.py


.PHONY: init test clean showoff


init:
	pip install -r $(REQUIREMENTS_FILE)


test:
	$(PY) $(FLAGS) $(TEST_SCRIPT)


clean:
	rm -rf $(SRC_DIR)/__pycache__ $(TESTS_DIR)/__pycache__


showoff:
	$(PY) $(FLAGS) $(VISUALISER_SCRIPT) -e $(TEST_PUZZLE) &
	$(PY) $(FLAGS) $(VISUALISER_SCRIPT) -s $(TEST_PUZZLE) &
	$(PY) $(FLAGS) $(SOLVER_SCRIPT) $(TEST_PUZZLE) &
