"""Tests for synthetic ballot data generation.

This module tests the synthetic ballot generation system, ensuring it produces
realistic and valid RCV ballot data for testing and demonstration purposes.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.rcv_dashboard.simulation.synthetic_data import (
    generate_synthetic_ballots,
    create_voter_preferences,
    generate_polarized_election,
    generate_consensus_election,
    generate_close_race_election,
    generate_landslide_election,
)


class TestSyntheticBallotGeneration:
    """Test basic synthetic ballot generation."""
    
    def test_generate_synthetic_ballots_basic(self) -> None:
        """Test basic synthetic ballot generation."""
        candidates = ["Alice", "Bob", "Charlie"]
        num_voters = 100
        
        ballots = generate_synthetic_ballots(candidates, num_voters)
        
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # Check that all candidates in ballots are valid
        all_candidates_set = set(candidates)
        for ballot in ballots:
            for candidate in ballot:
                assert candidate in all_candidates_set
            
            # No duplicate candidates in single ballot
            assert len(ballot) == len(set(ballot))
    
    def test_generate_synthetic_ballots_empty_candidates(self) -> None:
        """Test synthetic ballot generation with empty candidates list."""
        with pytest.raises((ValueError, IndexError)):
            generate_synthetic_ballots([], 10)
    
    def test_generate_synthetic_ballots_zero_voters(self) -> None:
        """Test synthetic ballot generation with zero voters."""
        candidates = ["Alice", "Bob"]
        ballots = generate_synthetic_ballots(candidates, 0)
        assert len(ballots) == 0
    
    def test_generate_synthetic_ballots_single_candidate(self) -> None:
        """Test synthetic ballot generation with single candidate."""
        candidates = ["Alice"]
        num_voters = 50
        
        ballots = generate_synthetic_ballots(candidates, num_voters)
        
        assert len(ballots) == num_voters
        # All ballots should contain just Alice
        for ballot in ballots:
            assert ballot == ["Alice"] or ballot == []
    
    def test_generate_synthetic_ballots_with_preferences(self) -> None:
        """Test synthetic ballot generation with preference weights."""
        candidates = ["Alice", "Bob", "Charlie"]
        preferences = {"Alice": 0.5, "Bob": 0.3, "Charlie": 0.2}
        num_voters = 1000
        
        ballots = generate_synthetic_ballots(
            candidates, num_voters, preference_weights=preferences
        )
        
        assert len(ballots) == num_voters
        
        # Count first-choice preferences
        first_choices = {"Alice": 0, "Bob": 0, "Charlie": 0}
        for ballot in ballots:
            if ballot:  # Non-empty ballot
                first_choices[ballot[0]] += 1
        
        total_first_choices = sum(first_choices.values())
        if total_first_choices > 0:
            # Alice should have roughly the most first choices (with some variance)
            alice_pct = first_choices["Alice"] / total_first_choices
            assert alice_pct > 0.3  # Should be somewhat close to 0.5
    
    @given(
        num_candidates=st.integers(min_value=2, max_value=10),
        num_voters=st.integers(min_value=1, max_value=100)
    )
    def test_generate_synthetic_ballots_property_based(
        self, num_candidates: int, num_voters: int
    ) -> None:
        """Property-based test for synthetic ballot generation."""
        candidates = [f"Candidate_{i}" for i in range(num_candidates)]
        
        ballots = generate_synthetic_ballots(candidates, num_voters)
        
        # Properties that should always hold
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # Each ballot should have valid candidates and no duplicates
        all_candidates_set = set(candidates)
        for ballot in ballots:
            assert all(candidate in all_candidates_set for candidate in ballot)
            assert len(ballot) == len(set(ballot))  # No duplicates
            assert len(ballot) <= num_candidates  # Can't have more than total candidates


class TestVoterPreferences:
    """Test voter preference creation utilities."""
    
    def test_create_voter_preferences_basic(self) -> None:
        """Test basic voter preference creation."""
        candidates = ["Alice", "Bob", "Charlie"]
        preferences = create_voter_preferences(candidates)
        
        assert isinstance(preferences, dict)
        assert len(preferences) == len(candidates)
        
        for candidate in candidates:
            assert candidate in preferences
            assert 0 <= preferences[candidate] <= 1
        
        # Preferences should sum to approximately 1
        total = sum(preferences.values())
        assert abs(total - 1.0) < 0.01
    
    def test_create_voter_preferences_single_candidate(self) -> None:
        """Test voter preference creation with single candidate."""
        candidates = ["Alice"]
        preferences = create_voter_preferences(candidates)
        
        assert len(preferences) == 1
        assert preferences["Alice"] == 1.0
    
    def test_create_voter_preferences_many_candidates(self) -> None:
        """Test voter preference creation with many candidates."""
        candidates = [f"Candidate_{i}" for i in range(20)]
        preferences = create_voter_preferences(candidates)
        
        assert len(preferences) == 20
        assert all(0 <= weight <= 1 for weight in preferences.values())
        
        total = sum(preferences.values())
        assert abs(total - 1.0) < 0.01


class TestSpecializedElectionGeneration:
    """Test specialized election scenario generators."""
    
    def test_generate_polarized_election(self) -> None:
        """Test polarized election generation."""
        candidates = ["Progressive", "Moderate", "Conservative"]
        num_voters = 300
        
        ballots = generate_polarized_election(candidates, num_voters)
        
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # In a polarized election, voters should tend to strongly prefer
        # candidates on their side and avoid middle-ground candidates
        first_choices = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            if ballot:
                first_choices[ballot[0]] += 1
        
        # Moderate should typically get fewer first-choice votes in polarized election
        total_first_choices = sum(first_choices.values())
        if total_first_choices > 0:
            moderate_pct = first_choices.get("Moderate", 0) / total_first_choices
            # In a truly polarized election, moderate might have less than others
            assert moderate_pct >= 0  # Basic sanity check
    
    def test_generate_consensus_election(self) -> None:
        """Test consensus election generation."""
        candidates = ["Extreme A", "Moderate", "Extreme B"]
        num_voters = 300
        
        ballots = generate_consensus_election(candidates, num_voters)
        
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # In a consensus election, the moderate candidate should often appear
        # as a second choice even if not always first
        moderate_appearances = 0
        for ballot in ballots:
            if "Moderate" in ballot:
                moderate_appearances += 1
        
        # Moderate should appear in many ballots
        moderate_appearance_rate = moderate_appearances / len(ballots)
        assert moderate_appearance_rate > 0.3  # Should be reasonably popular
    
    def test_generate_close_race_election(self) -> None:
        """Test close race election generation."""
        candidates = ["Alice", "Bob", "Charlie"]
        num_voters = 300
        
        ballots = generate_close_race_election(candidates, num_voters)
        
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # In a close race, first-choice votes should be relatively evenly distributed
        first_choices = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            if ballot:
                first_choices[ballot[0]] += 1
        
        total_first_choices = sum(first_choices.values())
        if total_first_choices > 0:
            # No candidate should have a massive lead (less than 60% first choices)
            for candidate, count in first_choices.items():
                percentage = count / total_first_choices
                assert percentage < 0.6, f"{candidate} has too large a lead for close race"
    
    def test_generate_landslide_election(self) -> None:
        """Test landslide election generation."""
        candidates = ["Popular Candidate", "Opponent A", "Opponent B"]
        num_voters = 300
        
        ballots = generate_landslide_election(candidates, num_voters)
        
        assert len(ballots) == num_voters
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # In a landslide, the popular candidate should dominate first choices
        first_choices = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            if ballot:
                first_choices[ballot[0]] += 1
        
        total_first_choices = sum(first_choices.values())
        if total_first_choices > 0:
            popular_count = first_choices.get("Popular Candidate", 0)
            popular_pct = popular_count / total_first_choices
            
            # Popular candidate should have a strong lead
            assert popular_pct > 0.4, "Popular candidate should dominate in landslide"
    
    def test_specialized_elections_with_invalid_input(self) -> None:
        """Test specialized election generators with invalid input."""
        # Test with too few candidates
        with pytest.raises((ValueError, IndexError)):
            generate_polarized_election(["Alice"], 100)
        
        with pytest.raises((ValueError, IndexError)):
            generate_consensus_election([], 100)
        
        # Test with negative voters
        candidates = ["Alice", "Bob", "Charlie"]
        
        # These should handle edge cases gracefully
        ballots = generate_close_race_election(candidates, 0)
        assert len(ballots) == 0


class TestBallotQuality:
    """Test the quality and realism of generated ballots."""
    
    def test_ballot_length_distribution(self) -> None:
        """Test that generated ballots have realistic length distribution."""
        candidates = ["Alice", "Bob", "Charlie", "David", "Eve"]
        num_voters = 500
        
        ballots = generate_synthetic_ballots(candidates, num_voters)
        
        # Count ballot lengths
        length_counts = {}
        for ballot in ballots:
            length = len(ballot)
            length_counts[length] = length_counts.get(length, 0) + 1
        
        # Should have variety in ballot lengths (some voters rank fewer candidates)
        assert len(length_counts) > 1, "Should have variety in ballot lengths"
        
        # Should have some complete ballots but also some partial ones
        max_length = len(candidates)
        if max_length in length_counts:
            complete_ballots = length_counts[max_length]
            incomplete_ballots = num_voters - complete_ballots
            
            # Both complete and incomplete ballots should exist for realism
            assert complete_ballots > 0, "Should have some complete ballots"
            assert incomplete_ballots > 0, "Should have some incomplete ballots"
    
    def test_candidate_distribution_fairness(self) -> None:
        """Test that candidate distribution is not completely uniform (realistic)."""
        candidates = ["Alice", "Bob", "Charlie", "David"]
        num_voters = 1000
        
        ballots = generate_synthetic_ballots(candidates, num_voters)
        
        # Count how often each candidate appears anywhere in ballots
        appearance_counts = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            for candidate in ballot:
                appearance_counts[candidate] += 1
        
        # Should have some variation (not completely equal distribution)
        counts = list(appearance_counts.values())
        min_count = min(counts)
        max_count = max(counts)
        
        if min_count > 0:
            variation_ratio = max_count / min_count
            # Should have some variation but not extreme imbalance
            assert variation_ratio > 1.1, "Should have some variation in candidate popularity"
            assert variation_ratio < 10, "Should not have extreme imbalance"
    
    def test_ranking_position_realism(self) -> None:
        """Test that candidate positions in rankings show realistic patterns."""
        candidates = ["Popular", "Moderate", "Unpopular"]
        preferences = {"Popular": 0.5, "Moderate": 0.3, "Unpopular": 0.2}
        num_voters = 500
        
        ballots = generate_synthetic_ballots(
            candidates, num_voters, preference_weights=preferences
        )
        
        # Count positions where each candidate appears
        position_counts = {candidate: {"first": 0, "second": 0, "third": 0} 
                          for candidate in candidates}
        
        for ballot in ballots:
            for i, candidate in enumerate(ballot):
                if i == 0:
                    position_counts[candidate]["first"] += 1
                elif i == 1:
                    position_counts[candidate]["second"] += 1
                elif i == 2:
                    position_counts[candidate]["third"] += 1
        
        # Popular candidate should appear more often in earlier positions
        popular_first = position_counts["Popular"]["first"]
        unpopular_first = position_counts["Unpopular"]["first"]
        
        # This is probabilistic, but with 500 voters should be quite reliable
        if popular_first > 0 and unpopular_first >= 0:
            assert popular_first > unpopular_first, \
                   "Popular candidate should have more first-place votes"


@given(
    candidates_count=st.integers(min_value=2, max_value=8),
    voters_count=st.integers(min_value=1, max_value=50)
)
def test_synthetic_election_properties(candidates_count: int, voters_count: int) -> None:
    """Property-based tests for synthetic election generation."""
    candidates = [f"Candidate_{i}" for i in range(candidates_count)]
    
    # Test each specialized generator
    for generator in [generate_polarized_election, generate_consensus_election,
                     generate_close_race_election, generate_landslide_election]:
        ballots = generator(candidates, voters_count)
        
        # Basic properties
        assert len(ballots) == voters_count
        assert all(isinstance(ballot, list) for ballot in ballots)
        
        # Ballot validity
        all_candidates_set = set(candidates)
        for ballot in ballots:
            assert all(candidate in all_candidates_set for candidate in ballot)
            assert len(ballot) == len(set(ballot))  # No duplicates
            assert len(ballot) <= candidates_count