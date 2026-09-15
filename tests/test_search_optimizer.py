import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.search_optimizer import (
    is_tautology,
    optimize_pokemon_search,
    parse_search_term,
    remove_redundant_clauses,
)


def test_parse_search_term_splits_and_and_or():
    groups = parse_search_term("957,958,959&!shadow")
    assert groups == [frozenset({"957", "958", "959"}), frozenset({"!shadow"})]


def test_is_tautology_detects_literal_and_negation():
    assert is_tautology(frozenset({"shadow", "!shadow"}))
    assert not is_tautology(frozenset({"shadow", "alola"}))


def test_remove_redundant_clauses_drops_supersets():
    clauses = {frozenset({"1", "2"}), frozenset({"1", "2", "3"})}
    result = remove_redundant_clauses(clauses)
    assert result == {frozenset({"1", "2"})}


def test_remove_redundant_clauses_drops_tautologies():
    clauses = {frozenset({"shadow", "!shadow"}), frozenset({"1"})}
    result = remove_redundant_clauses(clauses)
    assert result == {frozenset({"1"})}


def test_optimize_single_term_is_unchanged_shape():
    result = optimize_pokemon_search(["957,958,959&!shadow"])
    # Both clauses should be present, joined with '&', order deterministic.
    assert "!shadow" in result
    assert "957,958,959" in result


def test_optimize_combines_multiple_terms_with_or():
    # Two independent terms should combine into a search matching either.
    result = optimize_pokemon_search(["1&!shadow", "2&shadow"])
    groups = result.split("&")
    # Every literal from both terms must appear somewhere in the result.
    flat = set(",".join(groups).split(","))
    assert {"1", "2"} <= flat


def test_optimize_empty_input_returns_empty_string():
    assert optimize_pokemon_search([]) == ""
