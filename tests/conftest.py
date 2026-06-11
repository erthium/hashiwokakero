"""Shared test helpers — fixture path roots."""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASIC_PUZZLE_DIR = FIXTURES_DIR / "basic"
DIFFICULT_PUZZLE_DIR = FIXTURES_DIR / "difficult"
TESTDATA_DIR = FIXTURES_DIR / "testdata"
