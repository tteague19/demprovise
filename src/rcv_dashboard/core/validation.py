"""Comprehensive ballot and election data validation.

This module provides validation functions for ensuring data quality and consistency
in RCV elections using Pydantic models for structured error reporting.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence, Set
from typing import Any

from .models import ValidationResult


def validate_ballots(ballots: Sequence[Sequence[str]]) -> ValidationResult:
    """Comprehensive validation of ballot data.
    
    Performs multiple validation checks:
    - Duplicate rankings within ballots
    - Candidate name consistency
    - Empty or malformed ballots
    - Statistical validation
    
    Args:
        ballots: List of ballots to validate
        
    Returns:
        Detailed validation results with errors and warnings
        
    Example:
        >>> ballots = [["Alice", "Bob"], ["Bob", "Alice"], ["Alice"]]
        >>> result = validate_ballots(ballots)
        >>> result.is_valid
        True
    """
    errors = []
    warnings = []
    
    if not ballots:
        errors.append("No ballots provided for validation")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            ballot_count=0,
            candidate_count=0,
        )
    
    # Check for empty ballots
    empty_ballots = 0
    for i, ballot in enumerate(ballots):
        if not ballot or not any(candidate.strip() for candidate in ballot):
            empty_ballots += 1
    
    if empty_ballots == len(ballots):
        errors.append("All ballots are empty")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            ballot_count=0,
            candidate_count=0,
        )
    elif empty_ballots > 0:
        warnings.append(f"Found {empty_ballots} empty ballots out of {len(ballots)} total")
    
    # Check for duplicate rankings within individual ballots
    duplicate_ballot_count = 0
    for i, ballot in enumerate(ballots):
        if ballot and check_for_duplicate_rankings(ballot):
            duplicate_ballot_count += 1
    
    if duplicate_ballot_count > 0:
        warnings.append(
            f"Found {duplicate_ballot_count} ballots with duplicate rankings. "
            "These may be excluded from processing."
        )
    
    # Collect all candidates
    all_candidates = get_all_candidates(ballots)
    
    if len(all_candidates) < 2:
        errors.append(f"Need at least 2 candidates for election, found {len(all_candidates)}")
    elif len(all_candidates) > 100:
        warnings.append(f"Large number of candidates ({len(all_candidates)}). Verify this is correct.")
    
    # Validate candidate names
    candidate_validation = validate_candidate_names(all_candidates)
    errors.extend(candidate_validation.errors)
    warnings.extend(candidate_validation.warnings)
    
    # Statistical validation
    stat_warnings = _perform_statistical_validation(ballots, all_candidates)
    warnings.extend(stat_warnings)
    
    # Check ballot length distribution
    ballot_lengths = [len(ballot) for ballot in ballots if ballot]
    if ballot_lengths:
        max_length = max(ballot_lengths)
        min_length = min(ballot_lengths)
        avg_length = sum(ballot_lengths) / len(ballot_lengths)
        
        if max_length > len(all_candidates):
            warnings.append(
                f"Some ballots are longer ({max_length}) than the number of candidates ({len(all_candidates)}). "
                "This suggests duplicate rankings or data errors."
            )
        
        if avg_length < 2 and len(all_candidates) > 2:
            warnings.append(
                f"Average ballot length is {avg_length:.1f}, which is quite short. "
                "Consider if voters are providing full preferences."
            )
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        candidate_count=len(all_candidates),
        ballot_count=len(ballots) - empty_ballots,
    )


def check_for_duplicate_rankings(ballot: Sequence[str]) -> bool:
    """Check if a ballot has duplicate candidate rankings.
    
    Args:
        ballot: Single ballot with candidate preferences
        
    Returns:
        True if ballot contains duplicates, False otherwise
        
    Example:
        >>> check_for_duplicate_rankings(["Alice", "Bob", "Alice"])
        True
        >>> check_for_duplicate_rankings(["Alice", "Bob", "Charlie"])
        False
    """
    if not ballot:
        return False
    
    # Clean and normalize candidate names for comparison
    cleaned_candidates = [candidate.strip().lower() for candidate in ballot if candidate.strip()]
    return len(cleaned_candidates) != len(set(cleaned_candidates))


def get_all_candidates(ballots: Sequence[Sequence[str]]) -> set[str]:
    """Extract all unique candidate names from ballots.
    
    Args:
        ballots: List of ballots, each ballot is a list of candidate names
        
    Returns:
        Set of all unique candidate names (cleaned and normalized)
        
    Example:
        >>> ballots = [["Alice", "Bob"], ["Bob", "Charlie"], ["Alice"]]
        >>> candidates = get_all_candidates(ballots)
        >>> sorted(candidates)
        ['Alice', 'Bob', 'Charlie']
    """
    candidates = set()
    for ballot in ballots:
        for candidate in ballot:
            cleaned = candidate.strip()
            if cleaned:  # Only add non-empty candidate names
                candidates.add(cleaned)
    return candidates


def validate_candidate_names(candidates: Set[str]) -> ValidationResult:
    """Validate candidate names for potential issues.
    
    Args:
        candidates: Set of candidate names to validate
        
    Returns:
        Validation result focusing on candidate name issues
        
    Example:
        >>> candidates = {"Alice Johnson", "Bob Smith", "Charlie Brown"}
        >>> result = validate_candidate_names(candidates)
        >>> result.is_valid
        True
    """
    errors = []
    warnings = []
    
    if not candidates:
        errors.append("No candidate names provided")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            candidate_count=0,
        )
    
    # Check for suspiciously similar names (potential duplicates)
    candidates_list = list(candidates)
    similar_pairs = []
    
    for i, name1 in enumerate(candidates_list):
        for name2 in candidates_list[i+1:]:
            if _are_names_similar(name1, name2):
                similar_pairs.append((name1, name2))
    
    if similar_pairs:
        warnings.append(
            f"Found {len(similar_pairs)} pairs of similar candidate names. "
            f"Examples: {similar_pairs[:3]}. Check for typos or duplicates."
        )
    
    # Check for extremely long names
    long_names = [name for name in candidates if len(name) > 100]
    if long_names:
        warnings.append(
            f"Found {len(long_names)} extremely long candidate names. "
            "This may indicate data formatting issues."
        )
    
    # Check for names with unusual characters
    unusual_char_names = []
    for name in candidates:
        if any(ord(char) > 127 for char in name):  # Non-ASCII characters
            unusual_char_names.append(name)
    
    if unusual_char_names:
        warnings.append(
            f"Found {len(unusual_char_names)} names with non-ASCII characters. "
            "Ensure proper encoding is maintained."
        )
    
    # Check for names that are just numbers or very short
    problematic_names = []
    for name in candidates:
        if len(name.strip()) < 2:
            problematic_names.append(name)
        elif name.strip().isdigit():
            problematic_names.append(name)
    
    if problematic_names:
        warnings.append(
            f"Found {len(problematic_names)} potentially problematic names: {problematic_names[:5]}. "
            "Check for data formatting issues."
        )
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        candidate_count=len(candidates),
    )


def _are_names_similar(name1: str, name2: str, threshold: float = 0.8) -> bool:
    """Check if two candidate names are suspiciously similar.
    
    Uses simple character-based similarity to catch potential typos.
    
    Args:
        name1: First candidate name
        name2: Second candidate name
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if names are similar enough to be suspicious
    """
    # Simple character overlap similarity
    name1_lower = name1.lower().strip()
    name2_lower = name2.lower().strip()
    
    if name1_lower == name2_lower:
        return True
    
    # Check for character overlap
    chars1 = set(name1_lower)
    chars2 = set(name2_lower)
    
    if not chars1 or not chars2:
        return False
    
    overlap = len(chars1.intersection(chars2))
    total_unique = len(chars1.union(chars2))
    
    similarity = overlap / total_unique if total_unique > 0 else 0.0
    
    return similarity > threshold and abs(len(name1) - len(name2)) <= 2


def _perform_statistical_validation(
    ballots: Sequence[Sequence[str]], 
    all_candidates: set[str]
) -> list[str]:
    """Perform statistical validation checks on ballot data.
    
    Args:
        ballots: List of all ballots
        all_candidates: Set of all candidates
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if not ballots or not all_candidates:
        return warnings
    
    # Count how often each candidate appears in first position
    first_choice_counts = Counter()
    for ballot in ballots:
        if ballot:
            first_choice_counts[ballot[0]] += 1
    
    # Check for candidates that never appear as first choice
    never_first = all_candidates - set(first_choice_counts.keys())
    if never_first and len(never_first) < len(all_candidates):
        warnings.append(
            f"{len(never_first)} candidates never appear as first choice: {sorted(list(never_first))[:5]}"
        )
    
    # Check for extreme first-choice dominance
    if first_choice_counts:
        max_first_choice = max(first_choice_counts.values())
        total_ballots = len(ballots)
        dominance_ratio = max_first_choice / total_ballots
        
        if dominance_ratio > 0.8:
            dominant_candidate = max(first_choice_counts, key=first_choice_counts.get)
            warnings.append(
                f"One candidate ({dominant_candidate}) has {dominance_ratio:.1%} of first-choice votes. "
                "This suggests a very one-sided election."
            )
    
    # Count total mentions of each candidate across all positions
    mention_counts = Counter()
    for ballot in ballots:
        for candidate in ballot:
            mention_counts[candidate] += 1
    
    # Check for candidates mentioned very rarely
    total_mentions = sum(mention_counts.values())
    rarely_mentioned = []
    
    for candidate in all_candidates:
        mention_ratio = mention_counts[candidate] / total_mentions if total_mentions > 0 else 0
        if mention_ratio < 0.05:  # Less than 5% of total mentions
            rarely_mentioned.append(candidate)
    
    if rarely_mentioned:
        warnings.append(
            f"{len(rarely_mentioned)} candidates are mentioned very rarely: {rarely_mentioned[:5]}"
        )
    
    return warnings


def validate_election_completeness(ballots: Sequence[Sequence[str]]) -> ValidationResult:
    """Validate that an election has sufficient data for meaningful results.
    
    Args:
        ballots: List of ballots for the election
        
    Returns:
        Validation result focused on election completeness
        
    Example:
        >>> ballots = [["Alice", "Bob"], ["Bob", "Alice"]] * 50  # 100 ballots
        >>> result = validate_election_completeness(ballots)
        >>> result.is_valid
        True
    """
    errors = []
    warnings = []
    
    if not ballots:
        errors.append("No ballots provided for election")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            ballot_count=0,
            candidate_count=0,
        )
    
    valid_ballots = [ballot for ballot in ballots if ballot and any(c.strip() for c in ballot)]
    candidates = get_all_candidates(valid_ballots)
    
    # Check minimum ballot count
    min_ballots_needed = max(len(candidates) * 2, 10)  # At least 2 per candidate, minimum 10
    if len(valid_ballots) < min_ballots_needed:
        warnings.append(
            f"Only {len(valid_ballots)} ballots for {len(candidates)} candidates. "
            f"Consider having at least {min_ballots_needed} ballots for reliable results."
        )
    
    # Check for sufficient preference depth
    ballots_with_multiple_choices = sum(1 for ballot in valid_ballots if len(ballot) > 1)
    single_choice_ratio = (len(valid_ballots) - ballots_with_multiple_choices) / len(valid_ballots)
    
    if single_choice_ratio > 0.8:
        warnings.append(
            f"{single_choice_ratio:.1%} of ballots contain only first-choice votes. "
            "RCV works best when voters provide multiple preferences."
        )
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        candidate_count=len(candidates),
        ballot_count=len(valid_ballots),
    )