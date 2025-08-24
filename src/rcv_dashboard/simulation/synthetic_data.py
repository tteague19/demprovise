"""Synthetic ballot data generation for testing and demonstration.

This module provides algorithms for generating realistic ballot data with
various voting patterns, preference correlations, and demographic models.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..core.models import BallotData


@dataclass
class VoterBloc:
    """Configuration for a group of voters with similar preferences.
    
    Attributes:
        name: Descriptive name for this voter bloc
        size: Number of voters in this bloc
        preference_weights: Mapping of candidate names to preference strengths (0-1)
        preference_order: Default ranking order for this bloc
        randomness: How much random variation to add (0-1, 0=deterministic)
        issue_positions: Optional issue positions that affect candidate preferences
    """
    name: str
    size: int
    preference_weights: dict[str, float]
    preference_order: list[str] | None = None
    randomness: float = 0.1
    issue_positions: dict[str, float] | None = None


def generate_synthetic_ballots(
    candidates: Sequence[str],
    num_voters: int,
    preference_weights: dict[str, float] | None = None,
    correlation_matrix: np.ndarray | None = None,
    random_seed: int | None = None
) -> list[list[str]]:
    """Generate synthetic ballots with realistic voting patterns.
    
    Creates ballots using preference weights and optional correlation patterns
    to simulate realistic voter behavior in ranked choice elections.
    
    Args:
        candidates: List of candidate names
        num_voters: Total number of ballots to generate
        preference_weights: Base popularity weights for each candidate (0-1)
        correlation_matrix: Correlation matrix for candidate preferences
        random_seed: Seed for reproducible generation
        
    Returns:
        List of ballots, each ballot is a list of candidate names in rank order
        
    Example:
        >>> candidates = ["Alice", "Bob", "Charlie"]
        >>> weights = {"Alice": 0.4, "Bob": 0.35, "Charlie": 0.25}
        >>> ballots = generate_synthetic_ballots(candidates, 100, weights)
        >>> len(ballots)
        100
    """
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    candidate_list = list(candidates)
    num_candidates = len(candidate_list)
    
    if num_candidates < 2:
        raise ValueError("At least 2 candidates required for ballot generation")
    
    # Initialize default uniform weights if none provided
    if preference_weights is None:
        preference_weights = {name: 1.0 / num_candidates for name in candidate_list}
    
    # Normalize weights to sum to 1
    total_weight = sum(preference_weights.values())
    if total_weight > 0:
        preference_weights = {
            name: weight / total_weight 
            for name, weight in preference_weights.items()
        }
    
    # Generate correlation matrix if not provided
    if correlation_matrix is None:
        correlation_matrix = _generate_default_correlation_matrix(num_candidates)
    
    ballots = []
    
    for _ in range(num_voters):
        ballot = _generate_single_ballot(
            candidate_list, 
            preference_weights, 
            correlation_matrix
        )
        ballots.append(ballot)
    
    return ballots


def generate_ballots_from_blocs(voter_blocs: Sequence[VoterBloc]) -> list[list[str]]:
    """Generate ballots based on predefined voter bloc configurations.
    
    This approach allows for more sophisticated modeling of voter behavior
    by defining distinct groups with different preference patterns.
    
    Args:
        voter_blocs: List of voter bloc configurations
        
    Returns:
        List of ballots representing all voter blocs
        
    Example:
        >>> progressive_bloc = VoterBloc(
        ...     name="Progressive",
        ...     size=40,
        ...     preference_weights={"Green": 0.6, "Liberal": 0.3, "Conservative": 0.1}
        ... )
        >>> ballots = generate_ballots_from_blocs([progressive_bloc])
    """
    if not voter_blocs:
        raise ValueError("At least one voter bloc is required")
    
    all_ballots = []
    
    for bloc in voter_blocs:
        if bloc.size <= 0:
            continue
        
        # Get all unique candidates across blocs
        all_candidates = list(bloc.preference_weights.keys())
        
        for _ in range(bloc.size):
            ballot = _generate_bloc_ballot(bloc, all_candidates)
            all_ballots.append(ballot)
    
    # Shuffle to mix bloc patterns
    random.shuffle(all_ballots)
    return all_ballots


def create_polarized_election(
    candidates: Sequence[str],
    num_voters: int,
    polarization_strength: float = 0.7,
    random_seed: int | None = None
) -> list[list[str]]:
    """Generate ballots for a polarized election with strong preference divisions.
    
    Creates voting patterns where voters have strong preferences and
    limited crossover between different candidate supporters.
    
    Args:
        candidates: List of candidate names
        num_voters: Total number of ballots to generate
        polarization_strength: How polarized the election is (0-1, 1=maximum polarization)
        random_seed: Seed for reproducible generation
        
    Returns:
        List of ballots with polarized voting patterns
        
    Example:
        >>> candidates = ["Left", "Center", "Right"]
        >>> ballots = create_polarized_election(candidates, 150, 0.8)
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    candidate_list = list(candidates)
    if len(candidate_list) < 2:
        raise ValueError("At least 2 candidates required")
    
    # Create voter blocs with strong preferences
    blocs = []
    voters_per_candidate = num_voters // len(candidate_list)
    remaining_voters = num_voters % len(candidate_list)
    
    for i, primary_candidate in enumerate(candidate_list):
        # Give this bloc extra voters if there are remainder votes
        bloc_size = voters_per_candidate + (1 if i < remaining_voters else 0)
        
        # Create preference weights favoring this candidate
        weights = {}
        remaining_weight = 1.0 - polarization_strength
        other_candidates = [c for c in candidate_list if c != primary_candidate]
        
        weights[primary_candidate] = polarization_strength
        
        # Distribute remaining weight among other candidates
        if other_candidates:
            weight_per_other = remaining_weight / len(other_candidates)
            for candidate in other_candidates:
                weights[candidate] = weight_per_other
        
        bloc = VoterBloc(
            name=f"{primary_candidate} Supporters",
            size=bloc_size,
            preference_weights=weights,
            randomness=0.3 * (1.0 - polarization_strength)  # Less randomness when more polarized
        )
        blocs.append(bloc)
    
    return generate_ballots_from_blocs(blocs)


def create_consensus_vs_polarizing_election(
    consensus_candidate: str,
    polarizing_candidate: str,
    other_candidates: Sequence[str],
    num_voters: int,
    consensus_appeal: float = 0.6,
    random_seed: int | None = None
) -> list[list[str]]:
    """Generate ballots showing consensus vs polarizing candidate dynamics.
    
    Creates an election where one candidate has broad second-choice appeal
    while another has strong first-choice support but limited transfers.
    
    Args:
        consensus_candidate: Candidate with broad appeal
        polarizing_candidate: Candidate with strong base but limited transfers
        other_candidates: Additional candidates in the race
        num_voters: Total number of ballots to generate
        consensus_appeal: How much broader appeal the consensus candidate has (0-1)
        random_seed: Seed for reproducible generation
        
    Returns:
        List of ballots demonstrating consensus vs polarizing dynamics
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    all_candidates = [consensus_candidate, polarizing_candidate] + list(other_candidates)
    
    # Create distinct voter blocs
    blocs = []
    
    # Polarizing candidate's base (strong support, few second choices given to others)
    base_size = int(num_voters * 0.3)
    base_weights = {consensus_candidate: 0.1, polarizing_candidate: 0.8}
    for candidate in other_candidates:
        base_weights[candidate] = 0.1 / len(other_candidates) if other_candidates else 0
    
    blocs.append(VoterBloc(
        name="Polarizing Base",
        size=base_size,
        preference_weights=base_weights,
        randomness=0.2
    ))
    
    # Consensus candidate's direct supporters
    consensus_direct_size = int(num_voters * 0.25)
    consensus_weights = {
        consensus_candidate: 0.6,
        polarizing_candidate: 0.1
    }
    for candidate in other_candidates:
        consensus_weights[candidate] = 0.3 / len(other_candidates) if other_candidates else 0
    
    blocs.append(VoterBloc(
        name="Consensus Direct",
        size=consensus_direct_size,
        preference_weights=consensus_weights,
        randomness=0.3
    ))
    
    # Voters who prefer others first but consensus candidate second
    remaining_voters = num_voters - base_size - consensus_direct_size
    
    if other_candidates:
        voters_per_other = remaining_voters // len(other_candidates)
        
        for i, primary_candidate in enumerate(other_candidates):
            bloc_size = voters_per_other + (1 if i < remaining_voters % len(other_candidates) else 0)
            
            # These voters prefer someone else first, consensus second, polarizing last
            other_weights = {
                primary_candidate: 0.5,
                consensus_candidate: 0.3 * consensus_appeal,
                polarizing_candidate: 0.1
            }
            
            # Distribute remaining weight
            remaining = 1.0 - sum(other_weights.values())
            other_others = [c for c in other_candidates if c != primary_candidate]
            if other_others:
                weight_per_other_other = remaining / len(other_others)
                for candidate in other_others:
                    other_weights[candidate] = weight_per_other_other
            
            blocs.append(VoterBloc(
                name=f"{primary_candidate} to Consensus",
                size=bloc_size,
                preference_weights=other_weights,
                randomness=0.4
            ))
    
    return generate_ballots_from_blocs(blocs)


def create_close_race_ballots(
    candidates: Sequence[str],
    num_voters: int,
    vote_spread: float = 0.1,
    random_seed: int | None = None
) -> list[list[str]]:
    """Generate ballots for a very close, competitive election.
    
    Creates voting patterns where multiple candidates are competitive
    and the outcome depends heavily on vote transfers.
    
    Args:
        candidates: List of candidate names
        num_voters: Total number of ballots to generate
        vote_spread: How close the race is (lower = closer race)
        random_seed: Seed for reproducible generation
        
    Returns:
        List of ballots creating a close, competitive election
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    candidate_list = list(candidates)
    if len(candidate_list) < 3:
        raise ValueError("At least 3 candidates required for close race simulation")
    
    # Create nearly equal base weights with small variations
    base_weight = 1.0 / len(candidate_list)
    weights = {}
    
    for i, candidate in enumerate(candidate_list):
        # Add small random variations within the spread
        variation = random.uniform(-vote_spread/2, vote_spread/2)
        weights[candidate] = base_weight + variation
    
    # Normalize to ensure they sum to 1
    total = sum(weights.values())
    weights = {name: weight/total for name, weight in weights.items()}
    
    # Generate ballots with high preference mixing
    return generate_synthetic_ballots(
        candidate_list,
        num_voters,
        weights,
        correlation_matrix=_create_high_mixing_correlation_matrix(len(candidate_list))
    )


def create_landslide_ballots(
    winner_candidate: str,
    other_candidates: Sequence[str],
    num_voters: int,
    winner_strength: float = 0.6,
    random_seed: int | None = None
) -> list[list[str]]:
    """Generate ballots for a landslide election with clear winner.
    
    Creates voting patterns where one candidate has overwhelming support
    and wins decisively, possibly in the first round.
    
    Args:
        winner_candidate: The candidate who should win decisively
        other_candidates: Other candidates in the race
        num_voters: Total number of ballots to generate
        winner_strength: How strong the winner's support is (0-1)
        random_seed: Seed for reproducible generation
        
    Returns:
        List of ballots creating a landslide victory
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    other_list = list(other_candidates)
    all_candidates = [winner_candidate] + other_list
    
    # Winner gets the specified strength, others split the remainder
    weights = {winner_candidate: winner_strength}
    
    if other_list:
        remaining_weight = 1.0 - winner_strength
        weight_per_other = remaining_weight / len(other_list)
        
        for candidate in other_list:
            weights[candidate] = weight_per_other
    
    # Generate ballots with winner preference
    return generate_synthetic_ballots(all_candidates, num_voters, weights)


def _generate_single_ballot(
    candidates: list[str],
    preference_weights: dict[str, float],
    correlation_matrix: np.ndarray
) -> list[str]:
    """Generate a single ballot using preference weights and correlations."""
    # Generate correlated random preferences
    num_candidates = len(candidates)
    raw_scores = np.random.multivariate_normal(
        mean=np.zeros(num_candidates),
        cov=correlation_matrix
    )
    
    # Apply preference weights
    weighted_scores = []
    for i, candidate in enumerate(candidates):
        base_weight = preference_weights.get(candidate, 0.0)
        # Convert weight to bias in the random score
        bias = np.log(base_weight + 0.001)  # Add small constant to avoid log(0)
        final_score = raw_scores[i] + bias
        weighted_scores.append((final_score, candidate))
    
    # Sort by score (highest first) to create ranking
    weighted_scores.sort(reverse=True, key=lambda x: x[0])
    
    # Extract candidate names in rank order
    ballot = [candidate for _, candidate in weighted_scores]
    
    # Occasionally create incomplete ballots (some voters don't rank everyone)
    if random.random() < 0.15:  # 15% chance of incomplete ballot
        cutoff = random.randint(1, max(2, len(ballot) - 1))
        ballot = ballot[:cutoff]
    
    return ballot


def _generate_bloc_ballot(bloc: VoterBloc, all_candidates: list[str]) -> list[str]:
    """Generate a single ballot for a voter bloc."""
    # If the bloc has a predefined preference order, use it as base
    if bloc.preference_order:
        base_order = [c for c in bloc.preference_order if c in all_candidates]
        # Add any missing candidates at the end
        missing = [c for c in all_candidates if c not in base_order]
        base_order.extend(missing)
        ballot = base_order.copy()
        
        # Apply randomness by occasionally swapping adjacent candidates
        if bloc.randomness > 0:
            for i in range(len(ballot) - 1):
                if random.random() < bloc.randomness:
                    # Swap adjacent candidates
                    ballot[i], ballot[i + 1] = ballot[i + 1], ballot[i]
    else:
        # Use preference weights to generate ballot
        ballot = _generate_single_ballot(
            all_candidates,
            bloc.preference_weights,
            _generate_default_correlation_matrix(len(all_candidates))
        )
    
    return ballot


def _generate_default_correlation_matrix(num_candidates: int) -> np.ndarray:
    """Generate a default correlation matrix for candidate preferences."""
    # Create weak positive correlations (candidates somewhat similar)
    correlation = 0.1
    matrix = np.full((num_candidates, num_candidates), correlation)
    
    # Set diagonal to 1.0 (perfect self-correlation)
    np.fill_diagonal(matrix, 1.0)
    
    return matrix


def _create_high_mixing_correlation_matrix(num_candidates: int) -> np.ndarray:
    """Create correlation matrix that encourages preference mixing."""
    # Create slightly negative correlations to encourage vote spreading
    correlation = -0.05
    matrix = np.full((num_candidates, num_candidates), correlation)
    np.fill_diagonal(matrix, 1.0)
    
    return matrix


def create_ballot_data_from_synthetic(
    ballots: list[list[str]], 
    validation_enabled: bool = True
) -> BallotData:
    """Convert synthetic ballots to validated BallotData object.
    
    Args:
        ballots: List of synthetic ballots
        validation_enabled: Whether to run validation on the data
        
    Returns:
        BallotData object ready for RCV processing
        
    Example:
        >>> ballots = generate_synthetic_ballots(["A", "B", "C"], 50)
        >>> ballot_data = create_ballot_data_from_synthetic(ballots)
        >>> ballot_data.total_ballots
        50
    """
    if not ballots:
        raise ValueError("No ballots provided")
    
    # Extract all unique candidates
    all_candidates = set()
    valid_ballots = []
    invalid_count = 0
    
    for ballot in ballots:
        if not ballot:
            invalid_count += 1
            continue
        
        # Check for duplicate preferences
        if len(ballot) != len(set(ballot)):
            invalid_count += 1
            continue
        
        # Clean candidate names
        cleaned_ballot = [str(candidate).strip() for candidate in ballot if str(candidate).strip()]
        
        if not cleaned_ballot:
            invalid_count += 1
            continue
        
        valid_ballots.append(cleaned_ballot)
        all_candidates.update(cleaned_ballot)
    
    if not valid_ballots:
        raise ValueError("No valid ballots after processing")
    
    return BallotData(
        ballots=valid_ballots,
        candidates=all_candidates,
        total_ballots=len(valid_ballots),
        invalid_ballots=invalid_count
    )