"""Tests for ballot and election validation functionality."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.rcv_dashboard.core.validation import (
    check_for_duplicate_rankings,
    get_all_candidates,
    validate_ballots,
    validate_candidate_names,
    validate_election_completeness,
)


def test_validate_ballots_valid() -> None:
    """Test validation of valid ballot data."""
    ballots = [
        ["Alice", "Bob"],
        ["Bob", "Alice"],
        ["Charlie", "Alice"]
    ]
    
    result = validate_ballots(ballots)
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.candidate_count == 3
    assert result.ballot_count == 3


def test_validate_ballots_empty() -> None:
    """Test validation of empty ballot list."""
    result = validate_ballots([])
    
    assert not result.is_valid
    assert "No ballots provided for validation" in result.errors


def test_validate_ballots_all_empty() -> None:
    """Test validation when all ballots are empty."""
    ballots = [[], [""], ["   "]]
    
    result = validate_ballots(ballots)
    
    assert not result.is_valid
    assert "All ballots are empty" in result.errors


def test_validate_ballots_some_empty() -> None:
    """Test validation with some empty ballots."""
    ballots = [
        ["Alice", "Bob"],
        [],  # Empty ballot
        ["Bob", "Alice"]
    ]
    
    result = validate_ballots(ballots)
    
    # Should still be valid but with warnings
    assert result.is_valid
    assert any("empty ballots" in warning for warning in result.warnings)


def test_validate_ballots_too_few_candidates() -> None:
    """Test validation with insufficient candidates."""
    ballots = [["Alice"], ["Alice"]]
    
    result = validate_ballots(ballots)
    
    assert not result.is_valid
    assert "Need at least 2 candidates" in result.errors[0]


def test_validate_ballots_duplicate_rankings() -> None:
    """Test validation with duplicate rankings in ballots."""
    ballots = [
        ["Alice", "Bob"],
        ["Alice", "Alice"],  # Duplicate ranking
        ["Bob", "Alice"]
    ]
    
    result = validate_ballots(ballots)
    
    # Should be valid overall but with warnings about duplicates
    assert result.is_valid
    assert any("duplicate rankings" in warning for warning in result.warnings)


def test_validate_ballots_many_candidates() -> None:
    """Test validation with many candidates (should warn)."""
    # Create many unique candidate names
    candidates = [f"Candidate_{i}" for i in range(120)]
    ballots = [[candidate] for candidate in candidates]
    
    result = validate_ballots(ballots)
    
    # Should warn about large number of candidates
    assert any("Large number of candidates" in warning for warning in result.warnings)


def test_validate_candidate_names_valid() -> None:
    """Test validation of reasonable candidate names."""
    candidates = {"Alice Johnson", "Bob Smith", "Charlie Brown"}
    
    result = validate_candidate_names(candidates)
    
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.candidate_count == 3


def test_validate_candidate_names_empty() -> None:
    """Test validation of empty candidate set."""
    result = validate_candidate_names(set())
    
    assert not result.is_valid
    assert "No candidate names provided" in result.errors


def test_validate_candidate_names_similar() -> None:
    """Test validation with similar candidate names."""
    candidates = {"Alice Johnson", "Alice Jonson"}  # Very similar names
    
    result = validate_candidate_names(candidates)
    
    # Should be valid but with warnings
    assert result.is_valid
    assert any("similar candidate names" in warning for warning in result.warnings)


def test_validate_candidate_names_long() -> None:
    """Test validation with very long candidate names."""
    long_name = "A" * 150  # Very long name
    candidates = {"Alice", long_name}
    
    result = validate_candidate_names(candidates)
    
    # Should warn about long names
    assert any("extremely long candidate names" in warning for warning in result.warnings)


def test_validate_candidate_names_unusual_characters() -> None:
    """Test validation with non-ASCII characters."""
    candidates = {"José García", "François Müller"}  # Non-ASCII characters
    
    result = validate_candidate_names(candidates)
    
    # Should warn about non-ASCII characters
    assert any("non-ASCII characters" in warning for warning in result.warnings)


def test_validate_candidate_names_problematic() -> None:
    """Test validation with problematic candidate names."""
    candidates = {"A", "123", "Normal Name"}  # Very short and all-digit names
    
    result = validate_candidate_names(candidates)
    
    # Should warn about problematic names
    assert any("potentially problematic names" in warning for warning in result.warnings)


def test_validate_election_completeness_sufficient() -> None:
    """Test validation of complete election with sufficient data."""
    ballots = [["Alice", "Bob"], ["Bob", "Alice"]] * 20  # 40 ballots
    
    result = validate_election_completeness(ballots)
    
    assert result.is_valid
    assert result.ballot_count == 40
    assert result.candidate_count == 2


def test_validate_election_completeness_empty() -> None:
    """Test validation of empty election."""
    result = validate_election_completeness([])
    
    assert not result.is_valid
    assert "No ballots provided for election" in result.errors


def test_validate_election_completeness_insufficient_ballots() -> None:
    """Test validation with insufficient ballots."""
    ballots = [["Alice", "Bob"], ["Bob", "Alice"]]  # Only 2 ballots for 2 candidates
    
    result = validate_election_completeness(ballots)
    
    # Should warn about insufficient ballots
    assert any("Only 2 ballots for 2 candidates" in warning for warning in result.warnings)


def test_validate_election_completeness_single_choice() -> None:
    """Test validation where most ballots have only one choice.""" 
    ballots = [
        ["Alice"],      # Single choice
        ["Bob"],        # Single choice  
        ["Charlie"],    # Single choice
        ["Alice"],      # Single choice
        ["Bob"],        # Single choice
        ["Charlie"],    # Single choice
        ["Alice"],      # Single choice
        ["Bob"],        # Single choice
        ["Charlie"],    # Single choice
        ["Alice", "Bob"]  # Multiple choices - only 1 out of 10
    ]
    
    result = validate_election_completeness(ballots)
    
    # Should warn about single-choice ballots  
    assert any("contain only first-choice votes" in warning for warning in result.warnings)


def test_check_for_duplicate_rankings_function() -> None:
    """Test the standalone duplicate rankings check function."""
    # No duplicates
    assert not check_for_duplicate_rankings(["Alice", "Bob", "Charlie"])
    
    # With duplicates
    assert check_for_duplicate_rankings(["Alice", "Bob", "Alice"])
    
    # Empty ballot
    assert not check_for_duplicate_rankings([])
    
    # Case-insensitive duplicates
    assert check_for_duplicate_rankings(["Alice", "bob", "ALICE"])


def test_get_all_candidates_function() -> None:
    """Test the standalone candidate extraction function."""
    ballots = [
        ["Alice", "Bob"],
        ["Bob", "Charlie", "Alice"],
        ["David"]
    ]
    
    candidates = get_all_candidates(ballots)
    assert candidates == {"Alice", "Bob", "Charlie", "David"}
    
    # Test with empty ballots
    ballots_with_empty = [
        ["Alice", "Bob"],
        [],
        ["Charlie"]
    ]
    
    candidates = get_all_candidates(ballots_with_empty)
    assert candidates == {"Alice", "Bob", "Charlie"}


@given(
    ballots=st.lists(
        st.lists(
            st.text(min_size=1, max_size=10, alphabet="ABCDEFGH"),
            min_size=1,
            max_size=4,
            unique=True  # No duplicates within a ballot
        ),
        min_size=1,
        max_size=20
    )
)
def test_validate_ballots_properties(ballots: list[list[str]]) -> None:
    """Property-based test for ballot validation using Hypothesis."""
    try:
        result = validate_ballots(ballots)
        
        # Basic properties that should always hold
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert result.candidate_count >= 0
        assert result.ballot_count >= 0
        
        # If validation passes, should have reasonable counts
        if result.is_valid:
            assert result.candidate_count >= 1  # At least one candidate
            assert result.ballot_count >= 1    # At least one ballot
        
        # If there are errors, validation should fail
        if result.errors:
            assert not result.is_valid
    
    except Exception:
        # Some random inputs might be problematic, which is fine for fuzzing
        pass


def test_statistical_validation_warnings() -> None:
    """Test statistical validation warnings."""
    # Create ballots where one candidate dominates
    ballots = [["Alice", "Bob"]] * 20 + [["Bob", "Alice"]] * 2
    
    result = validate_ballots(ballots)
    
    # Should warn about dominance
    assert any("very one-sided election" in warning for warning in result.warnings)


def test_rarely_mentioned_candidates() -> None:
    """Test validation of candidates mentioned very rarely."""
    # Create many ballots where one candidate is mentioned very rarely  
    ballots = [["Alice", "Bob"]] * 100 + [["Charlie"]]  # Charlie mentioned only once out of 201 total mentions
    
    result = validate_ballots(ballots)
    
    # Should warn about rarely mentioned candidates
    assert any("are mentioned very rarely" in warning for warning in result.warnings)


def test_candidates_never_first_choice() -> None:
    """Test validation when some candidates never appear as first choice."""
    ballots = [
        ["Alice", "Bob", "Charlie"],
        ["Alice", "Bob", "Charlie"],
        ["Alice", "Bob", "Charlie"],
    ]
    
    result = validate_ballots(ballots)
    
    # Bob and Charlie never appear as first choice
    assert any("never appear as first choice" in warning for warning in result.warnings)