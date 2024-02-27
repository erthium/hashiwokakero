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
PRODUCTION_SCRIPT := $(SRC_DIR)/production.py
MAPPER_SCRIPT := $(SRC_DIR)/difficulty_mapper.py

TEST_SCRIPT := $(TESTS_DIR)/hashi_test.py


DATABASE_DIR := database
EASY_PUZZLES_DIR := $(DATABASE_DIR)/easy
INTERMEDIATE_PUZZLES_DIR := $(DATABASE_DIR)/intermediate
HARD_PUZZLES_DIR := $(DATABASE_DIR)/hard
UNORDERED_PUZZLES_DIR := $(DATABASE_DIR)/unordered

P := 10
W := 15
H := 15

sure=0

.PHONY: init freeze test clean showoff see produce map nuke_db

init:
	pip install -r $(REQUIREMENTS_FILE)


freeze:
	pip freeze > $(REQUIREMENTS_FILE)


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


produce:
	$(PY) $(FLAGS) $(PRODUCTION_SCRIPT) $(W) $(H) $(P) 


map:
	$(PY) $(FLAGS) $(MAPPER_SCRIPT)


nuke_db:
	[ $(sure) -eq 1 ] && rm -f $(EASY_PUZZLES_DIR)/* $(INTERMEDIATE_PUZZLES_DIR)/* $(HARD_PUZZLES_DIR)/* $(UNORDERED_PUZZLES_DIR)/*
