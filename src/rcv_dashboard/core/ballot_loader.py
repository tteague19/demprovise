"""Ballot loading and validation functionality.

This module handles loading ballot data from various file formats (CSV, Excel)
and converting them into validated Pydantic models for processing.
"""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from .models import BallotData, ValidationResult


def load_ballots_from_file(file_path: str | Path) -> BallotData:
    """Load ballots from a CSV or Excel file.
    
    Args:
        file_path: Path to the ballot file
        
    Returns:
        Validated ballot data ready for processing
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or data is invalid
        
    Example:
        >>> ballots = load_ballots_from_file("election_data.csv")
        >>> ballots.total_ballots
        150
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine file type and load accordingly
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() in {'.xlsx', '.xls'}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {file_path.suffix}. "
            "Supported formats: .csv, .xlsx, .xls"
        )
    
    return _process_dataframe(df)


def load_ballots_from_uploaded_file(uploaded_file: Any) -> BallotData:
    """Load ballots from a Streamlit uploaded file object.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Validated ballot data ready for processing
        
    Raises:
        ValueError: If file format is unsupported or data is invalid
        
    Example:
        >>> # In Streamlit app:
        >>> uploaded = st.file_uploader("Upload ballots")
        >>> if uploaded:
        ...     ballots = load_ballots_from_uploaded_file(uploaded)
    """
    if uploaded_file is None:
        raise ValueError("No file provided")
    
    file_name = getattr(uploaded_file, 'name', 'unknown')
    file_extension = Path(file_name).suffix.lower()
    
    # Read file content into bytes
    file_content = uploaded_file.read()
    
    # Reset file pointer if possible (for Streamlit compatibility)
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    
    # Load based on file extension
    if file_extension == '.csv':
        df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
    elif file_extension in {'.xlsx', '.xls'}:
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError(
            f"Unsupported file format: {file_extension}. "
            "Supported formats: .csv, .xlsx, .xls"
        )
    
    return _process_dataframe(df)


def _process_dataframe(df: pd.DataFrame) -> BallotData:
    """Process a pandas DataFrame into validated ballot data.
    
    Args:
        df: Raw DataFrame from file
        
    Returns:
        Validated ballot data
        
    Raises:
        ValueError: If DataFrame format is invalid
    """
    if df.empty:
        raise ValueError("File contains no data")
    
    # Standardize column names
    df = standardize_column_names(df)
    
    # Validate basic structure
    validation_result = validate_ballot_format(df)
    if not validation_result.is_valid:
        error_msg = "; ".join(validation_result.errors)
        raise ValueError(f"Invalid ballot format: {error_msg}")
    
    # Extract ballots and candidates
    ballots, candidates, invalid_count = _extract_ballots_and_candidates(df)
    
    return BallotData(
        ballots=ballots,
        candidates=candidates,
        total_ballots=len(ballots),
        invalid_ballots=invalid_count,
    )


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to consistent format.
    
    Handles various common naming conventions:
    - "Choice 1", "Choice 2", etc.
    - "Rank 1", "Rank 2", etc.
    - "1st Choice", "2nd Choice", etc.
    - "First", "Second", etc.
    
    Args:
        df: DataFrame with potentially varied column names
        
    Returns:
        DataFrame with standardized column names (choice_1, choice_2, etc.)
        
    Example:
        >>> df = pd.DataFrame({"1st Choice": ["Alice"], "2nd Choice": ["Bob"]})
        >>> standardized = standardize_column_names(df)
        >>> list(standardized.columns)
        ['choice_1', 'choice_2']
    """
    df = df.copy()
    
    # Common patterns for preference columns
    column_patterns = [
        # "Choice 1", "Choice 2", etc.
        (r'^choice\s*(\d+)$', 'choice_{}'),
        # "Rank 1", "Rank 2", etc.
        (r'^rank\s*(\d+)$', 'choice_{}'),
        # "1st Choice", "2nd Choice", etc.
        (r'^(\d+)(?:st|nd|rd|th)\s*choice$', 'choice_{}'),
        # "First", "Second", etc. (limited set)
        (r'^first$', 'choice_1'),
        (r'^second$', 'choice_2'),
        (r'^third$', 'choice_3'),
        (r'^fourth$', 'choice_4'),
        (r'^fifth$', 'choice_5'),
    ]
    
    import re
    
    new_columns = []
    for col in df.columns:
        col_str = str(col).lower().strip()
        renamed = False
        
        for pattern, replacement in column_patterns:
            if pattern in ['first', 'second', 'third', 'fourth', 'fifth']:
                if col_str == pattern:
                    new_columns.append(replacement)
                    renamed = True
                    break
            else:
                match = re.match(pattern, col_str, re.IGNORECASE)
                if match:
                    if '{}' in replacement:
                        new_columns.append(replacement.format(match.group(1)))
                    else:
                        new_columns.append(replacement)
                    renamed = True
                    break
        
        if not renamed:
            # If no pattern matches, keep original but clean it up
            clean_name = re.sub(r'[^\w]', '_', col_str).lower()
            new_columns.append(clean_name)
    
    df.columns = new_columns
    return df


def validate_ballot_format(df: pd.DataFrame) -> ValidationResult:
    """Validate the format of ballot data in a DataFrame.
    
    Args:
        df: DataFrame containing ballot data
        
    Returns:
        Validation result with errors and warnings
        
    Example:
        >>> df = pd.DataFrame({"choice_1": ["Alice", "Bob"], "choice_2": ["Bob", "Alice"]})
        >>> result = validate_ballot_format(df)
        >>> result.is_valid
        True
    """
    errors = []
    warnings = []
    
    # Check if DataFrame is empty
    if df.empty:
        errors.append("No data found in file")
        return ValidationResult(is_valid=False, errors=errors)
    
    # Check for minimum columns (at least one choice column)
    choice_columns = [col for col in df.columns if col.startswith('choice_')]
    if not choice_columns:
        errors.append("No preference columns found. Expected columns like 'choice_1', 'choice_2', etc.")
        return ValidationResult(is_valid=False, errors=errors)
    
    # Check for reasonable number of choice columns
    if len(choice_columns) > 20:
        warnings.append(f"Large number of preference columns ({len(choice_columns)}). This may indicate formatting issues.")
    
    # Validate choice column sequence
    expected_numbers = set(range(1, len(choice_columns) + 1))
    actual_numbers = set()
    
    for col in choice_columns:
        try:
            num = int(col.split('_')[1])
            actual_numbers.add(num)
        except (IndexError, ValueError):
            errors.append(f"Invalid choice column name: {col}")
    
    if actual_numbers != expected_numbers:
        missing = expected_numbers - actual_numbers
        extra = actual_numbers - expected_numbers
        
        if missing:
            warnings.append(f"Missing choice columns for ranks: {sorted(missing)}")
        if extra:
            warnings.append(f"Unexpected choice column ranks: {sorted(extra)}")
    
    # Check for completely empty rows
    non_empty_rows = 0
    for _, row in df.iterrows():
        if any(pd.notna(val) and str(val).strip() for val in row[choice_columns]):
            non_empty_rows += 1
    
    if non_empty_rows == 0:
        errors.append("No valid ballot data found. All rows appear to be empty.")
    elif non_empty_rows < len(df) * 0.9:  # Less than 90% of rows have data
        warnings.append(f"Only {non_empty_rows} out of {len(df)} rows contain ballot data")
    
    # Check for reasonable candidate names
    all_candidates = set()
    for col in choice_columns:
        candidates_in_col = df[col].dropna().astype(str).str.strip()
        candidates_in_col = candidates_in_col[candidates_in_col != '']
        all_candidates.update(candidates_in_col)
    
    if len(all_candidates) < 2:
        errors.append(f"Need at least 2 candidates, found {len(all_candidates)}")
    elif len(all_candidates) > 50:
        warnings.append(f"Large number of candidates ({len(all_candidates)}). Verify this is correct.")
    
    # Check for very long candidate names (possible data issues)
    long_names = [name for name in all_candidates if len(str(name)) > 100]
    if long_names:
        warnings.append(f"Found {len(long_names)} very long candidate names. Check for data issues.")
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        candidate_count=len(all_candidates),
        ballot_count=non_empty_rows,
    )


def _extract_ballots_and_candidates(df: pd.DataFrame) -> tuple[list[list[str]], set[str], int]:
    """Extract ballot preferences and candidate list from DataFrame.
    
    Args:
        df: Processed DataFrame with standardized columns
        
    Returns:
        Tuple of (ballots, candidates, invalid_ballot_count)
    """
    choice_columns = sorted([col for col in df.columns if col.startswith('choice_')])
    ballots = []
    all_candidates = set()
    invalid_count = 0
    
    for _, row in df.iterrows():
        ballot = []
        
        # Extract preferences in order
        for col in choice_columns:
            value = row[col]
            
            if pd.notna(value):
                candidate = str(value).strip()
                if candidate:  # Non-empty candidate name
                    ballot.append(candidate)
                    all_candidates.add(candidate)
        
        # Only include non-empty ballots
        if ballot:
            # Check for duplicate preferences in this ballot
            if len(ballot) == len(set(ballot)):
                ballots.append(ballot)
            else:
                # Skip ballots with duplicate preferences
                invalid_count += 1
        else:
            invalid_count += 1
    
    return ballots, all_candidates, invalid_count


def get_all_candidates(ballots: Sequence[Sequence[str]]) -> set[str]:
    """Extract all unique candidate names from ballots.
    
    Args:
        ballots: List of ballots, each ballot is a list of candidate names
        
    Returns:
        Set of all unique candidate names
        
    Example:
        >>> ballots = [["Alice", "Bob"], ["Bob", "Charlie"], ["Alice"]]
        >>> candidates = get_all_candidates(ballots)
        >>> sorted(candidates)
        ['Alice', 'Bob', 'Charlie']
    """
    candidates = set()
    for ballot in ballots:
        candidates.update(ballot)
    return candidates


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
    return len(ballot) != len(set(ballot))