PY := python3
FLAGS := -b
SRC_DIR := hashi
TESTS_DIR := tests
PUZZLES_DIR := $(SRC_DIR)/puzzles

SHOW_PUZZLE = $(PUZZLES_DIR)/puzzle_3.csv
MANUAL_TEST_PUZZLE := $(PUZZLES_DIR)/puzzle_2.csv

REQUIREMENTS_FILE := requirements.txt

GENERATOR_SCRIPT := $(SRC_DIR)/generator.py
SOLVER_SCRIPT := $(SRC_DIR)/solver.py
VISUALISER_SCRIPT := $(SRC_DIR)/visualiser.py

TEST_SCRIPT := $(TESTS_DIR)/hashi_test.py


.PHONY: init test clean showoff see


init:
	pip install -r $(REQUIREMENTS_FILE)


test:
	$(PY) $(FLAGS) $(TEST_SCRIPT)


clean:
	rm -rf $(SRC_DIR)/__pycache__ $(TESTS_DIR)/__pycache__


showoff:
	$(PY) $(FLAGS) $(VISUALISER_SCRIPT) -e $(SHOW_PUZZLE) &
	$(PY) $(FLAGS) $(VISUALISER_SCRIPT) -s $(SHOW_PUZZLE) &
	$(PY) $(FLAGS) $(SOLVER_SCRIPT) $(SHOW_PUZZLE) &


see:
	$(PY) $(FLAGS) $(VISUALISER_SCRIPT) -s $(MANUAL_TEST_PUZZLE) &
	$(PY) $(FLAGS) $(SOLVER_SCRIPT) $(MANUAL_TEST_PUZZLE) &
