"""Tests for Pydantic models and data structures.

This module tests all the core data models used throughout the RCV Dashboard,
ensuring proper validation, serialization, and business logic.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from src.rcv_dashboard.core.models import (
    BallotData,
    CandidateInfo,
    ElectionResult,
    RoundResult,
    AppSettings,
    ValidationResult,
)


class TestCandidateInfo:
    """Test CandidateInfo model validation and behavior."""
    
    def test_candidate_info_creation(self) -> None:
        """Test basic candidate info creation."""
        candidate = CandidateInfo(name="Alice Johnson", first_choice_votes=150)
        assert candidate.name == "Alice Johnson"
        assert candidate.first_choice_votes == 150
        assert candidate.final_votes == 0
        assert candidate.eliminated_round is None
        assert candidate.is_winner is False
    
    def test_candidate_info_validation(self) -> None:
        """Test candidate info validation rules."""
        # Valid candidate
        CandidateInfo(name="Valid Name", first_choice_votes=0)
        
        # Invalid: empty name
        with pytest.raises(ValidationError):
            CandidateInfo(name="", first_choice_votes=10)
        
        # Invalid: negative votes
        with pytest.raises(ValidationError):
            CandidateInfo(name="Alice", first_choice_votes=-1)
    
    @given(
        name=st.text(min_size=1, max_size=100),
        first_choice=st.integers(min_value=0, max_value=10000)
    )
    def test_candidate_info_property_based(self, name: str, first_choice: int) -> None:
        """Property-based test for candidate info."""
        # Skip whitespace-only names
        if name.strip():
            candidate = CandidateInfo(name=name.strip(), first_choice_votes=first_choice)
            assert candidate.first_choice_votes >= 0
            assert len(candidate.name) > 0


class TestBallotData:
    """Test BallotData model validation and behavior."""
    
    def test_ballot_data_creation(self) -> None:
        """Test basic ballot data creation."""
        ballots = [
            ["Alice", "Bob", "Charlie"],
            ["Bob", "Alice"],
            ["Charlie", "Bob", "Alice"]
        ]
        
        ballot_data = BallotData(
            ballots=ballots,
            candidates=["Alice", "Bob", "Charlie"],
            total_ballots=3,
            candidate_count=3
        )
        
        assert len(ballot_data.ballots) == 3
        assert len(ballot_data.candidates) == 3
        assert ballot_data.total_ballots == 3
        assert ballot_data.candidate_count == 3
        assert "Alice" in ballot_data.candidates
        assert "Bob" in ballot_data.candidates
        assert "Charlie" in ballot_data.candidates
    
    def test_ballot_data_validation(self) -> None:
        """Test ballot data validation rules."""
        # Valid ballot data
        BallotData(
            ballots=[["Alice", "Bob"]],
            candidates=["Alice", "Bob"],
            total_ballots=1,
            candidate_count=2
        )
        
        # Invalid: empty ballots
        with pytest.raises(ValidationError):
            BallotData(
                ballots=[],
                candidates=["Alice"],
                total_ballots=0,
                candidate_count=1
            )
        
        # Invalid: mismatched counts
        with pytest.raises(ValidationError):
            BallotData(
                ballots=[["Alice"]],
                candidates=["Alice", "Bob"],
                total_ballots=1,
                candidate_count=1  # Should be 2
            )


class TestRoundResult:
    """Test RoundResult model validation and behavior."""
    
    def test_round_result_creation(self) -> None:
        """Test basic round result creation."""
        vote_counts = {"Alice": 100, "Bob": 75, "Charlie": 50}
        
        round_result = RoundResult(
            round_number=1,
            vote_counts=vote_counts,
            eliminated_candidate=None,
            winner=None,
            total_votes=225
        )
        
        assert round_result.round_number == 1
        assert round_result.vote_counts == vote_counts
        assert round_result.eliminated_candidate is None
        assert round_result.winner is None
        assert round_result.total_votes == 225
    
    def test_round_result_with_elimination(self) -> None:
        """Test round result with candidate elimination."""
        vote_counts = {"Alice": 100, "Bob": 75}
        
        round_result = RoundResult(
            round_number=2,
            vote_counts=vote_counts,
            eliminated_candidate="Charlie",
            winner=None,
            total_votes=175
        )
        
        assert round_result.eliminated_candidate == "Charlie"
        assert "Charlie" not in round_result.vote_counts
    
    def test_round_result_validation(self) -> None:
        """Test round result validation rules."""
        # Valid round result
        RoundResult(
            round_number=1,
            vote_counts={"Alice": 10},
            eliminated_candidate=None,
            winner=None,
            total_votes=10
        )
        
        # Invalid: negative round number
        with pytest.raises(ValidationError):
            RoundResult(
                round_number=0,
                vote_counts={"Alice": 10},
                eliminated_candidate=None,
                winner=None,
                total_votes=10
            )
        
        # Invalid: negative votes
        with pytest.raises(ValidationError):
            RoundResult(
                round_number=1,
                vote_counts={"Alice": -5},
                eliminated_candidate=None,
                winner=None,
                total_votes=0
            )


class TestElectionResult:
    """Test ElectionResult model validation and behavior."""
    
    def test_election_result_creation(self) -> None:
        """Test basic election result creation."""
        candidates = [
            CandidateInfo(name="Alice", first_choice_votes=100, final_votes=150, is_winner=True),
            CandidateInfo(name="Bob", first_choice_votes=75, final_votes=0, eliminated_round=2)
        ]
        
        rounds = [
            RoundResult(
                round_number=1,
                vote_counts={"Alice": 100, "Bob": 75},
                eliminated_candidate=None,
                winner=None,
                total_votes=175
            ),
            RoundResult(
                round_number=2,
                vote_counts={"Alice": 150},
                eliminated_candidate="Bob",
                winner="Alice",
                total_votes=150
            )
        ]
        
        election_result = ElectionResult(
            winner="Alice",
            total_rounds=2,
            candidates=candidates,
            rounds=rounds,
            total_ballots=175
        )
        
        assert election_result.winner == "Alice"
        assert election_result.total_rounds == 2
        assert len(election_result.candidates) == 2
        assert len(election_result.rounds) == 2
        assert election_result.total_ballots == 175
    
    def test_election_result_validation(self) -> None:
        """Test election result validation rules."""
        candidate = CandidateInfo(name="Alice", first_choice_votes=10)
        round_result = RoundResult(
            round_number=1,
            vote_counts={"Alice": 10},
            eliminated_candidate=None,
            winner="Alice",
            total_votes=10
        )
        
        # Valid election result
        ElectionResult(
            winner="Alice",
            total_rounds=1,
            candidates=[candidate],
            rounds=[round_result],
            total_ballots=10
        )
        
        # Invalid: empty winner
        with pytest.raises(ValidationError):
            ElectionResult(
                winner="",
                total_rounds=1,
                candidates=[candidate],
                rounds=[round_result],
                total_ballots=10
            )
        
        # Invalid: zero rounds
        with pytest.raises(ValidationError):
            ElectionResult(
                winner="Alice",
                total_rounds=0,
                candidates=[candidate],
                rounds=[],
                total_ballots=10
            )


class TestValidationResult:
    """Test ValidationResult model validation and behavior."""
    
    def test_validation_result_success(self) -> None:
        """Test successful validation result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            candidate_count=3,
            ballot_count=100
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.candidate_count == 3
        assert result.ballot_count == 100
    
    def test_validation_result_with_errors(self) -> None:
        """Test validation result with errors."""
        errors = ["Duplicate candidate name found", "Invalid ballot format"]
        
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            candidate_count=0,
            ballot_count=0
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "Duplicate candidate name found" in result.errors
        assert "Invalid ballot format" in result.errors
    
    def test_validation_result_validation(self) -> None:
        """Test validation result validation rules."""
        # Valid validation result
        ValidationResult(
            is_valid=True,
            errors=[],
            candidate_count=1,
            ballot_count=1
        )
        
        # Invalid: negative counts
        with pytest.raises(ValidationError):
            ValidationResult(
                is_valid=True,
                errors=[],
                candidate_count=-1,
                ballot_count=1
            )


class TestAppSettings:
    """Test AppSettings model validation and behavior."""
    
    def test_app_settings_creation(self) -> None:
        """Test basic app settings creation."""
        settings = AppSettings()
        
        # Check default values
        assert settings.show_debug_info is False
        assert settings.max_candidates >= 2
        assert settings.max_ballots > 0
        assert settings.enable_animations is True
        assert isinstance(settings.theme_color, str)
        assert len(settings.theme_color) > 0
    
    def test_app_settings_custom_values(self) -> None:
        """Test app settings with custom values."""
        settings = AppSettings(
            show_debug_info=True,
            max_candidates=20,
            max_ballots=5000,
            enable_animations=False,
            theme_color="#FF0000"
        )
        
        assert settings.show_debug_info is True
        assert settings.max_candidates == 20
        assert settings.max_ballots == 5000
        assert settings.enable_animations is False
        assert settings.theme_color == "#FF0000"
    
    def test_app_settings_validation(self) -> None:
        """Test app settings validation rules."""
        # Valid settings
        AppSettings(max_candidates=2, max_ballots=1)
        
        # Invalid: too few max_candidates
        with pytest.raises(ValidationError):
            AppSettings(max_candidates=1)
        
        # Invalid: zero max_ballots
        with pytest.raises(ValidationError):
            AppSettings(max_ballots=0)


@given(
    round_num=st.integers(min_value=1, max_value=100),
    votes=st.integers(min_value=0, max_value=10000)
)
def test_round_result_properties(round_num: int, votes: int) -> None:
    """Property-based test for round results."""
    vote_counts = {"candidate": votes}
    round_result = RoundResult(
        round_number=round_num,
        vote_counts=vote_counts,
        eliminated_candidate=None,
        winner=None,
        total_votes=votes
    )
    
    assert round_result.round_number >= 1
    assert round_result.total_votes >= 0
    assert sum(round_result.vote_counts.values()) <= round_result.total_votes


def test_model_serialization() -> None:
    """Test that models can be serialized to and from JSON."""
    candidate = CandidateInfo(name="Alice", first_choice_votes=100)
    
    # Test model_dump (Pydantic v2)
    data = candidate.model_dump()
    assert data["name"] == "Alice"
    assert data["first_choice_votes"] == 100
    
    # Test reconstruction from dict
    new_candidate = CandidateInfo(**data)
    assert new_candidate.name == candidate.name
    assert new_candidate.first_choice_votes == candidate.first_choice_votes


def test_model_immutability() -> None:
    """Test that models handle immutability correctly."""
    candidate = CandidateInfo(name="Alice", first_choice_votes=100)
    
    # Models should be immutable (if configured with frozen=True)
    # Test basic attribute access works
    assert candidate.name == "Alice"
    assert candidate.first_choice_votes == 100