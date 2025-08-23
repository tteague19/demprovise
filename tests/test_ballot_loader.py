"""Tests for ballot loading and file processing functionality."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.rcv_dashboard.core.ballot_loader import (
    check_for_duplicate_rankings,
    get_all_candidates,
    load_ballots_from_file,
    standardize_column_names,
    validate_ballot_format,
)


def test_standardize_column_names() -> None:
    """Test column name standardization for various formats."""
    # Test "Choice 1", "Choice 2" format
    df = pd.DataFrame({"Choice 1": ["Alice"], "Choice 2": ["Bob"]})
    result = standardize_column_names(df)
    assert list(result.columns) == ["choice_1", "choice_2"]
    
    # Test "1st Choice", "2nd Choice" format
    df = pd.DataFrame({"1st Choice": ["Alice"], "2nd Choice": ["Bob"]})
    result = standardize_column_names(df)
    assert list(result.columns) == ["choice_1", "choice_2"]
    
    # Test "Rank 1", "Rank 2" format
    df = pd.DataFrame({"Rank 1": ["Alice"], "Rank 2": ["Bob"]})
    result = standardize_column_names(df)
    assert list(result.columns) == ["choice_1", "choice_2"]
    
    # Test word formats
    df = pd.DataFrame({"First": ["Alice"], "Second": ["Bob"], "Third": ["Charlie"]})
    result = standardize_column_names(df)
    assert list(result.columns) == ["choice_1", "choice_2", "choice_3"]


def test_validate_ballot_format_valid() -> None:
    """Test validation of valid ballot formats."""
    df = pd.DataFrame({
        "choice_1": ["Alice", "Bob", "Charlie"],
        "choice_2": ["Bob", "Alice", "Alice"],
        "choice_3": ["Charlie", "Charlie", "Bob"]
    })
    
    result = validate_ballot_format(df)
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.candidate_count == 3
    assert result.ballot_count == 3


def test_validate_ballot_format_no_data() -> None:
    """Test validation with empty DataFrame."""
    df = pd.DataFrame()
    result = validate_ballot_format(df)
    
    assert not result.is_valid
    assert "No data found in file" in result.errors


def test_validate_ballot_format_no_choice_columns() -> None:
    """Test validation when no choice columns are found."""
    df = pd.DataFrame({"other_column": ["value1", "value2"]})
    result = validate_ballot_format(df)
    
    assert not result.is_valid
    assert "No preference columns found" in result.errors[0]


def test_validate_ballot_format_warnings() -> None:
    """Test validation warnings for edge cases."""
    # Create DataFrame with many choice columns (should warn)
    columns = {f"choice_{i}": [f"Candidate{i}"] for i in range(1, 25)}
    df = pd.DataFrame(columns)
    
    result = validate_ballot_format(df)
    assert any("Large number of preference columns" in warning for warning in result.warnings)


def test_get_all_candidates() -> None:
    """Test candidate extraction from ballots."""
    ballots = [
        ["Alice", "Bob"],
        ["Bob", "Charlie"],
        ["Alice", "Charlie"]
    ]
    
    candidates = get_all_candidates(ballots)
    assert candidates == {"Alice", "Bob", "Charlie"}


def test_get_all_candidates_empty() -> None:
    """Test candidate extraction from empty ballots."""
    candidates = get_all_candidates([])
    assert candidates == set()


def test_check_for_duplicate_rankings() -> None:
    """Test duplicate ranking detection."""
    # No duplicates
    assert not check_for_duplicate_rankings(["Alice", "Bob", "Charlie"])
    
    # With duplicates
    assert check_for_duplicate_rankings(["Alice", "Bob", "Alice"])
    
    # Empty ballot
    assert not check_for_duplicate_rankings([])
    
    # Case-sensitive (ballot_loader version doesn't do case normalization)
    assert not check_for_duplicate_rankings(["Alice", "alice", "ALICE"])
    # But exact case duplicates are caught
    assert check_for_duplicate_rankings(["Alice", "Alice"])


def test_load_ballots_from_file_csv() -> None:
    """Test loading ballots from CSV file."""
    # Create temporary CSV file
    csv_content = """Choice 1,Choice 2,Choice 3
Alice,Bob,Charlie
Bob,Alice,
Charlie,Alice,Bob"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
        
        # Test loading
        ballot_data = load_ballots_from_file(f.name)
        
        assert ballot_data.total_ballots == 3
        assert "Alice" in ballot_data.candidates
        assert "Bob" in ballot_data.candidates
        assert "Charlie" in ballot_data.candidates
    
    # Cleanup
    Path(f.name).unlink()


def test_load_ballots_from_file_excel() -> None:
    """Test loading ballots from Excel file."""
    # Create temporary Excel file
    df = pd.DataFrame({
        "Choice 1": ["Alice", "Bob"],
        "Choice 2": ["Bob", "Alice"]
    })
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        
        # Test loading
        ballot_data = load_ballots_from_file(f.name)
        
        assert ballot_data.total_ballots == 2
        assert ballot_data.candidates == {"Alice", "Bob"}
    
    # Cleanup
    Path(f.name).unlink()


def test_load_ballots_from_file_not_found() -> None:
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        load_ballots_from_file("nonexistent_file.csv")


def test_load_ballots_from_file_unsupported_format() -> None:
    """Test error handling for unsupported file formats."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("some content")
        f.flush()
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_ballots_from_file(f.name)
    
    # Cleanup
    Path(f.name).unlink()


class MockUploadedFile:
    """Mock Streamlit uploaded file for testing."""
    
    def __init__(self, content: str, name: str) -> None:
        self.content = content.encode('utf-8')
        self.name = name
        self._position = 0
    
    def read(self) -> bytes:
        return self.content
    
    def seek(self, position: int) -> None:
        self._position = position


def test_load_ballots_from_uploaded_file_csv() -> None:
    """Test loading ballots from uploaded CSV file."""
    csv_content = """Choice 1,Choice 2
Alice,Bob
Bob,Alice"""
    
    mock_file = MockUploadedFile(csv_content, "test.csv")
    
    # Import here to avoid issues if streamlit isn't available
    from src.rcv_dashboard.core.ballot_loader import load_ballots_from_uploaded_file
    
    ballot_data = load_ballots_from_uploaded_file(mock_file)
    
    assert ballot_data.total_ballots == 2
    assert ballot_data.candidates == {"Alice", "Bob"}


def test_load_ballots_from_uploaded_file_no_file() -> None:
    """Test error handling when no file is provided."""
    from src.rcv_dashboard.core.ballot_loader import load_ballots_from_uploaded_file
    
    with pytest.raises(ValueError, match="No file provided"):
        load_ballots_from_uploaded_file(None)


def test_load_ballots_from_uploaded_file_unsupported() -> None:
    """Test error handling for unsupported uploaded file format."""
    from src.rcv_dashboard.core.ballot_loader import load_ballots_from_uploaded_file
    
    mock_file = MockUploadedFile("content", "test.txt")
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_ballots_from_uploaded_file(mock_file)