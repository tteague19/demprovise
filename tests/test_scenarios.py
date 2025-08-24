"""Tests for demo election scenarios.

This module tests the pre-built election scenarios used for educational
demonstrations, ensuring they work correctly and provide valid RCV examples.
"""

from __future__ import annotations

import pytest

from src.rcv_dashboard.core.models import BallotData
from src.rcv_dashboard.simulation.scenarios import (
    get_scenario_list,
    load_scenario,
    DEMO_SCENARIOS,
)


class TestScenarioList:
    """Test scenario listing functionality."""
    
    def test_get_scenario_list(self) -> None:
        """Test that scenario list returns expected scenarios."""
        scenarios = get_scenario_list()
        
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        
        # Check that all expected scenarios are present
        expected_scenarios = [
            "Classic Spoiler Effect",
            "Polarized vs Consensus",
            "Close Three-Way Race",
            "Landslide Victory",
            "Comedy Competition",
            "Student Government",
            "City Council Race"
        ]
        
        for expected in expected_scenarios:
            assert expected in scenarios, f"Missing scenario: {expected}"
    
    def test_scenario_list_consistency(self) -> None:
        """Test that scenario list matches DEMO_SCENARIOS keys."""
        scenarios = get_scenario_list()
        demo_keys = list(DEMO_SCENARIOS.keys())
        
        # Should have same scenarios
        assert len(scenarios) == len(demo_keys)
        assert set(scenarios) == set(demo_keys)


class TestScenarioLoading:
    """Test individual scenario loading."""
    
    def test_load_classic_spoiler_scenario(self) -> None:
        """Test loading the Classic Spoiler Effect scenario."""
        ballot_data, description, analysis = load_scenario("Classic Spoiler Effect")
        
        # Check ballot data structure
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.total_ballots > 0
        assert ballot_data.candidate_count >= 3
        assert len(ballot_data.candidates) == ballot_data.candidate_count
        assert len(ballot_data.ballots) == ballot_data.total_ballots
        
        # Check description and analysis
        assert isinstance(description, str)
        assert len(description) > 100  # Should be substantial
        assert isinstance(analysis, str)
        assert len(analysis) > 100  # Should be substantial
        
        # Check for key spoiler effect elements
        assert any("spoiler" in candidate.lower() for candidate in ballot_data.candidates)
    
    def test_load_polarized_vs_consensus_scenario(self) -> None:
        """Test loading the Polarized vs Consensus scenario."""
        ballot_data, description, analysis = load_scenario("Polarized vs Consensus")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count >= 3
        assert "polarized" in description.lower() or "consensus" in description.lower()
        
        # Should have candidates representing different approaches
        candidates_lower = [c.lower() for c in ballot_data.candidates]
        assert len(candidates_lower) >= 3
    
    def test_load_close_three_way_race_scenario(self) -> None:
        """Test loading the Close Three-Way Race scenario."""
        ballot_data, description, analysis = load_scenario("Close Three-Way Race")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count == 3  # Should be exactly 3-way
        assert "close" in description.lower() or "three" in description.lower()
    
    def test_load_landslide_victory_scenario(self) -> None:
        """Test loading the Landslide Victory scenario."""
        ballot_data, description, analysis = load_scenario("Landslide Victory")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count >= 2
        assert "landslide" in description.lower() or "majority" in description.lower()
    
    def test_load_comedy_competition_scenario(self) -> None:
        """Test loading the Comedy Competition scenario."""
        ballot_data, description, analysis = load_scenario("Comedy Competition")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count >= 3
        assert ("comedy" in description.lower() or 
                "performance" in description.lower() or
                "show" in description.lower())
    
    def test_load_student_government_scenario(self) -> None:
        """Test loading the Student Government scenario."""
        ballot_data, description, analysis = load_scenario("Student Government")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count >= 3
        assert ("student" in description.lower() or 
                "campus" in description.lower() or
                "university" in description.lower())
    
    def test_load_city_council_race_scenario(self) -> None:
        """Test loading the City Council Race scenario."""
        ballot_data, description, analysis = load_scenario("City Council Race")
        
        assert isinstance(ballot_data, BallotData)
        assert ballot_data.candidate_count >= 3
        assert ("city" in description.lower() or 
                "council" in description.lower() or
                "municipal" in description.lower())
    
    def test_load_nonexistent_scenario(self) -> None:
        """Test loading a scenario that doesn't exist."""
        with pytest.raises(KeyError):
            load_scenario("Nonexistent Scenario")
    
    def test_load_empty_scenario_name(self) -> None:
        """Test loading with empty scenario name."""
        with pytest.raises(KeyError):
            load_scenario("")


class TestScenarioDataQuality:
    """Test the quality and consistency of scenario data."""
    
    def test_all_scenarios_load_successfully(self) -> None:
        """Test that all scenarios can be loaded without errors."""
        scenarios = get_scenario_list()
        
        for scenario_name in scenarios:
            try:
                ballot_data, description, analysis = load_scenario(scenario_name)
                
                # Basic validation
                assert isinstance(ballot_data, BallotData)
                assert isinstance(description, str)
                assert isinstance(analysis, str)
                assert len(description) > 0
                assert len(analysis) > 0
                
            except Exception as e:
                pytest.fail(f"Scenario '{scenario_name}' failed to load: {e}")
    
    def test_scenario_ballot_data_validity(self) -> None:
        """Test that all scenarios produce valid ballot data."""
        scenarios = get_scenario_list()
        
        for scenario_name in scenarios:
            ballot_data, _, _ = load_scenario(scenario_name)
            
            # Check ballot data constraints
            assert ballot_data.total_ballots > 0, f"{scenario_name}: No ballots"
            assert ballot_data.candidate_count >= 2, f"{scenario_name}: Too few candidates"
            assert len(ballot_data.candidates) == ballot_data.candidate_count, \
                   f"{scenario_name}: Candidate count mismatch"
            assert len(ballot_data.ballots) == ballot_data.total_ballots, \
                   f"{scenario_name}: Ballot count mismatch"
            
            # Check that all ballots are valid
            all_candidates_set = set(ballot_data.candidates)
            for i, ballot in enumerate(ballot_data.ballots):
                assert isinstance(ballot, list), f"{scenario_name}: Ballot {i} not a list"
                
                # Check that all candidates in ballot are valid
                for candidate in ballot:
                    assert candidate in all_candidates_set, \
                           f"{scenario_name}: Invalid candidate '{candidate}' in ballot {i}"
                
                # Check for duplicate candidates in single ballot
                assert len(ballot) == len(set(ballot)), \
                       f"{scenario_name}: Duplicate candidates in ballot {i}"
    
    def test_scenario_descriptions_quality(self) -> None:
        """Test that scenario descriptions meet quality standards."""
        scenarios = get_scenario_list()
        
        for scenario_name in scenarios:
            _, description, analysis = load_scenario(scenario_name)
            
            # Description quality checks
            assert len(description) >= 50, f"{scenario_name}: Description too short"
            assert len(description) <= 2000, f"{scenario_name}: Description too long"
            assert not description.isspace(), f"{scenario_name}: Description is just whitespace"
            
            # Analysis quality checks
            assert len(analysis) >= 50, f"{scenario_name}: Analysis too short"
            assert len(analysis) <= 3000, f"{scenario_name}: Analysis too long"
            assert not analysis.isspace(), f"{scenario_name}: Analysis is just whitespace"
    
    def test_scenario_educational_value(self) -> None:
        """Test that scenarios demonstrate different RCV concepts."""
        scenarios = get_scenario_list()
        
        # Collect all descriptions and analyses to check for diversity
        all_text = []
        
        for scenario_name in scenarios:
            _, description, analysis = load_scenario(scenario_name)
            combined_text = (description + " " + analysis).lower()
            all_text.append(combined_text)
        
        # Check that different RCV concepts are covered
        concepts_to_check = [
            ["spoiler", "third party", "split"],  # Spoiler effect
            ["majority", "consensus", "moderate"],  # Consensus building
            ["elimination", "round", "instant"],  # RCV mechanics
            ["preference", "ranking", "choice"],  # Voter preferences
            ["transfer", "redistrib", "realloc"],  # Vote transfers
        ]
        
        for concept_group in concepts_to_check:
            concept_found = False
            for text in all_text:
                if any(concept in text for concept in concept_group):
                    concept_found = True
                    break
            
            assert concept_found, f"No scenarios cover concept group: {concept_group}"
    
    def test_scenario_candidate_diversity(self) -> None:
        """Test that scenarios use diverse candidate names."""
        scenarios = get_scenario_list()
        all_candidates = set()
        
        for scenario_name in scenarios:
            ballot_data, _, _ = load_scenario(scenario_name)
            all_candidates.update(ballot_data.candidates)
        
        # Should have reasonable diversity in candidate names
        assert len(all_candidates) >= 15, "Scenarios should use diverse candidate names"
        
        # Check for different types of names
        candidate_names_lower = [name.lower() for name in all_candidates]
        
        # Should have some variety (not all single names, some descriptive, etc.)
        short_names = [name for name in candidate_names_lower if len(name) <= 10]
        long_names = [name for name in candidate_names_lower if len(name) > 10]
        
        assert len(short_names) > 0, "Should have some short candidate names"
        assert len(long_names) > 0, "Should have some descriptive candidate names"


class TestDemoScenariosConstant:
    """Test the DEMO_SCENARIOS constant structure."""
    
    def test_demo_scenarios_structure(self) -> None:
        """Test that DEMO_SCENARIOS has the expected structure."""
        assert isinstance(DEMO_SCENARIOS, dict)
        assert len(DEMO_SCENARIOS) > 0
        
        for scenario_name, scenario_data in DEMO_SCENARIOS.items():
            assert isinstance(scenario_name, str)
            assert len(scenario_name) > 0
            
            assert isinstance(scenario_data, dict)
            
            # Check required keys
            required_keys = ["ballots", "description", "analysis"]
            for key in required_keys:
                assert key in scenario_data, f"Missing key '{key}' in scenario '{scenario_name}'"
            
            # Check data types
            assert isinstance(scenario_data["ballots"], list)
            assert isinstance(scenario_data["description"], str)
            assert isinstance(scenario_data["analysis"], str)
            
            # Check that ballots are non-empty
            assert len(scenario_data["ballots"]) > 0
            
            # Check that each ballot is a list
            for ballot in scenario_data["ballots"]:
                assert isinstance(ballot, list)
    
    def test_demo_scenarios_completeness(self) -> None:
        """Test that all expected scenarios are in DEMO_SCENARIOS."""
        expected_scenarios = [
            "Classic Spoiler Effect",
            "Polarized vs Consensus", 
            "Close Three-Way Race",
            "Landslide Victory",
            "Comedy Competition",
            "Student Government",
            "City Council Race"
        ]
        
        for expected in expected_scenarios:
            assert expected in DEMO_SCENARIOS, f"Missing scenario: {expected}"