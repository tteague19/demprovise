"""Tests for file utility functions.

This module tests the file handling utilities including template generation,
export functionality, and file format conversions.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
import pandas as pd
from openpyxl import load_workbook

from src.rcv_dashboard.core.models import (
    BallotData,
    CandidateInfo,
    ElectionResult,
    RoundResult,
)
from src.rcv_dashboard.utils.file_utils import (
    create_ballot_template_csv,
    create_ballot_template_excel,
    export_results_to_csv,
    create_comprehensive_export_zip,
    validate_uploaded_file,
    extract_ballots_from_dataframe,
)


class TestBallotTemplateGeneration:
    """Test ballot template generation functions."""
    
    def test_create_ballot_template_csv_basic(self) -> None:
        """Test basic CSV template generation."""
        candidates = ["Alice Johnson", "Bob Smith", "Charlie Brown"]
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=5)
        
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # Parse the CSV to verify structure
        csv_str = csv_bytes.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Check header
        header = lines[0]
        assert "Choice 1" in header
        assert "Choice 2" in header
        assert "Choice 3" in header
        
        # Check that we have the right number of rows (header + samples)
        assert len(lines) == 6  # 1 header + 5 sample ballots
        
        # Check that candidate names appear in the samples
        csv_content = '\n'.join(lines[1:])  # Skip header
        for candidate in candidates:
            assert candidate in csv_content
    
    def test_create_ballot_template_csv_single_candidate(self) -> None:
        """Test CSV template generation with single candidate."""
        candidates = ["Alice"]
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=2)
        
        csv_str = csv_bytes.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Should have only one choice column
        header = lines[0]
        assert "Choice 1" in header
        assert "Choice 2" not in header
        
        # Alice should appear in samples
        assert "Alice" in csv_str
    
    def test_create_ballot_template_csv_no_samples(self) -> None:
        """Test CSV template generation with no sample ballots."""
        candidates = ["Alice", "Bob", "Charlie"]
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=0)
        
        csv_str = csv_bytes.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Should have only header
        assert len(lines) == 1
        assert "Choice 1" in lines[0]
    
    def test_create_ballot_template_excel_basic(self) -> None:
        """Test basic Excel template generation."""
        candidates = ["Alice Johnson", "Bob Smith", "Charlie Brown"]
        excel_bytes = create_ballot_template_excel(candidates, num_sample_ballots=5)
        
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        
        # Load the Excel file to verify structure
        workbook = load_workbook(io.BytesIO(excel_bytes))
        worksheet = workbook.active
        
        # Check header row
        assert worksheet.cell(1, 1).value == "Choice 1"
        assert worksheet.cell(1, 2).value == "Choice 2"
        assert worksheet.cell(1, 3).value == "Choice 3"
        
        # Check that we have sample data
        sample_values = []
        for row in range(2, 7):  # Rows 2-6 for 5 samples
            for col in range(1, 4):  # Columns 1-3
                value = worksheet.cell(row, col).value
                if value:
                    sample_values.append(value)
        
        # Should have candidate names in samples
        sample_text = ' '.join(str(v) for v in sample_values)
        for candidate in candidates:
            assert candidate in sample_text
    
    def test_create_ballot_template_excel_many_candidates(self) -> None:
        """Test Excel template generation with many candidates."""
        candidates = [f"Candidate {i}" for i in range(1, 11)]  # 10 candidates
        excel_bytes = create_ballot_template_excel(candidates, num_sample_ballots=3)
        
        workbook = load_workbook(io.BytesIO(excel_bytes))
        worksheet = workbook.active
        
        # Should have 10 choice columns
        for i in range(1, 11):
            assert worksheet.cell(1, i).value == f"Choice {i}"
        
        # 11th column should be empty
        assert worksheet.cell(1, 11).value is None


class TestResultsExport:
    """Test election results export functionality."""
    
    def create_sample_election_result(self) -> ElectionResult:
        """Create a sample election result for testing."""
        candidates = [
            CandidateInfo(
                name="Alice Johnson",
                first_choice_votes=120,
                final_votes=180,
                is_winner=True
            ),
            CandidateInfo(
                name="Bob Smith",
                first_choice_votes=100,
                final_votes=0,
                eliminated_round=2
            ),
            CandidateInfo(
                name="Charlie Brown",
                first_choice_votes=80,
                final_votes=0,
                eliminated_round=1
            )
        ]
        
        rounds = [
            RoundResult(
                round_number=1,
                vote_counts={"Alice Johnson": 120, "Bob Smith": 100, "Charlie Brown": 80},
                eliminated_candidate="Charlie Brown",
                winner=None,
                total_votes=300
            ),
            RoundResult(
                round_number=2,
                vote_counts={"Alice Johnson": 180, "Bob Smith": 120},
                eliminated_candidate="Bob Smith",
                winner="Alice Johnson",
                total_votes=300
            )
        ]
        
        return ElectionResult(
            winner="Alice Johnson",
            total_rounds=2,
            candidates=candidates,
            rounds=rounds,
            total_ballots=300
        )
    
    def test_export_results_to_csv_basic(self) -> None:
        """Test basic CSV results export."""
        election_result = self.create_sample_election_result()
        csv_bytes = export_results_to_csv(election_result)
        
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        csv_str = csv_bytes.decode('utf-8')
        
        # Check that key information is present
        assert "Alice Johnson" in csv_str
        assert "Bob Smith" in csv_str
        assert "Charlie Brown" in csv_str
        assert "Winner" in csv_str
        assert "180" in csv_str  # Alice's final votes
        
        # Should have multiple sections
        assert "ELECTION SUMMARY" in csv_str
        assert "ROUND RESULTS" in csv_str
        assert "CANDIDATE SUMMARY" in csv_str
    
    def test_export_results_csv_structure(self) -> None:
        """Test that exported CSV has correct structure."""
        election_result = self.create_sample_election_result()
        csv_bytes = export_results_to_csv(election_result)
        
        csv_str = csv_bytes.decode('utf-8')
        lines = csv_str.split('\n')
        
        # Should have multiple sections separated by empty lines
        assert len(lines) > 10  # Should be substantial
        
        # Check for section headers
        section_headers = [line for line in lines if line.startswith("=")]
        assert len(section_headers) >= 3  # Multiple sections
    
    def test_create_comprehensive_export_zip(self) -> None:
        """Test comprehensive ZIP export creation."""
        election_result = self.create_sample_election_result()
        zip_bytes = create_comprehensive_export_zip(election_result, charts_data={})
        
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        # Verify ZIP structure
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
            file_names = zip_file.namelist()
            
            # Should contain expected files
            assert any("results.csv" in name for name in file_names)
            assert any("summary.txt" in name for name in file_names)
            
            # Check that files are not empty
            for file_name in file_names:
                file_data = zip_file.read(file_name)
                assert len(file_data) > 0
    
    def test_create_comprehensive_export_zip_with_charts(self) -> None:
        """Test ZIP export with chart data."""
        election_result = self.create_sample_election_result()
        charts_data = {
            "vote_progression.png": b"fake_png_data",
            "sankey_diagram.html": b"<html>fake chart</html>"
        }
        
        zip_bytes = create_comprehensive_export_zip(election_result, charts_data)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
            file_names = zip_file.namelist()
            
            # Should contain chart files
            assert any("vote_progression.png" in name for name in file_names)
            assert any("sankey_diagram.html" in name for name in file_names)
            
            # Verify chart data
            png_data = zip_file.read([name for name in file_names if "vote_progression.png" in name][0])
            assert png_data == b"fake_png_data"


class TestFileValidation:
    """Test file validation functions."""
    
    def test_validate_uploaded_file_csv(self) -> None:
        """Test CSV file validation."""
        # Create a valid CSV in memory
        csv_content = "Choice 1,Choice 2,Choice 3\nAlice,Bob,Charlie\nBob,Alice,\n"
        csv_file = io.StringIO(csv_content)
        
        # Mock file object
        class MockFile:
            def __init__(self, content: str, name: str):
                self.content = content
                self.name = name
                self.size = len(content.encode())
            
            def read(self) -> bytes:
                return self.content.encode()
        
        mock_file = MockFile(csv_content, "test.csv")
        result = validate_uploaded_file(mock_file, max_size_mb=10)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["file_type"] == "csv"
        assert result["estimated_rows"] > 0
    
    def test_validate_uploaded_file_too_large(self) -> None:
        """Test file validation with oversized file."""
        csv_content = "Choice 1,Choice 2\nAlice,Bob\n"
        
        class MockFile:
            def __init__(self, content: str, name: str, size: int):
                self.content = content
                self.name = name
                self.size = size
            
            def read(self) -> bytes:
                return self.content.encode()
        
        # Mock a file that's too large
        mock_file = MockFile(csv_content, "test.csv", 50 * 1024 * 1024)  # 50MB
        result = validate_uploaded_file(mock_file, max_size_mb=10)
        
        assert result["is_valid"] is False
        assert any("too large" in error.lower() for error in result["errors"])
    
    def test_validate_uploaded_file_invalid_type(self) -> None:
        """Test file validation with invalid file type."""
        class MockFile:
            def __init__(self, content: str, name: str):
                self.content = content
                self.name = name
                self.size = len(content.encode())
            
            def read(self) -> bytes:
                return self.content.encode()
        
        mock_file = MockFile("some content", "test.txt")
        result = validate_uploaded_file(mock_file, max_size_mb=10)
        
        assert result["is_valid"] is False
        assert any("format" in error.lower() for error in result["errors"])


class TestBallotExtraction:
    """Test ballot extraction from DataFrames."""
    
    def test_extract_ballots_from_dataframe_basic(self) -> None:
        """Test basic ballot extraction from DataFrame."""
        # Create test DataFrame
        df = pd.DataFrame({
            'Choice 1': ['Alice', 'Bob', 'Charlie'],
            'Choice 2': ['Bob', 'Alice', 'Alice'],
            'Choice 3': ['Charlie', 'Charlie', 'Bob']
        })
        
        ballots, candidates = extract_ballots_from_dataframe(df)
        
        assert len(ballots) == 3
        assert set(candidates) == {'Alice', 'Bob', 'Charlie'}
        
        # Check ballot structure
        assert ballots[0] == ['Alice', 'Bob', 'Charlie']
        assert ballots[1] == ['Bob', 'Alice', 'Charlie']
        assert ballots[2] == ['Charlie', 'Alice', 'Bob']
    
    def test_extract_ballots_with_missing_values(self) -> None:
        """Test ballot extraction with missing values."""
        import numpy as np
        
        df = pd.DataFrame({
            'Choice 1': ['Alice', 'Bob', 'Charlie'],
            'Choice 2': ['Bob', np.nan, 'Alice'],
            'Choice 3': [np.nan, 'Alice', np.nan]
        })
        
        ballots, candidates = extract_ballots_from_dataframe(df)
        
        assert len(ballots) == 3
        assert set(candidates) == {'Alice', 'Bob', 'Charlie'}
        
        # Check that NaN values are handled
        assert ballots[0] == ['Alice', 'Bob']  # NaN removed
        assert ballots[1] == ['Bob', 'Alice']  # NaN removed
        assert ballots[2] == ['Charlie', 'Alice']  # NaN removed
    
    def test_extract_ballots_alternative_column_names(self) -> None:
        """Test ballot extraction with alternative column naming."""
        df = pd.DataFrame({
            '1st Choice': ['Alice', 'Bob'],
            '2nd Choice': ['Bob', 'Alice'],
            '3rd Choice': ['Charlie', 'Charlie']
        })
        
        ballots, candidates = extract_ballots_from_dataframe(df)
        
        assert len(ballots) == 2
        assert set(candidates) == {'Alice', 'Bob', 'Charlie'}
        
        assert ballots[0] == ['Alice', 'Bob', 'Charlie']
        assert ballots[1] == ['Bob', 'Alice', 'Charlie']
    
    def test_extract_ballots_rank_column_names(self) -> None:
        """Test ballot extraction with 'Rank' column naming."""
        df = pd.DataFrame({
            'Rank 1': ['Alice', 'Bob'],
            'Rank 2': ['Bob', 'Alice']
        })
        
        ballots, candidates = extract_ballots_from_dataframe(df)
        
        assert len(ballots) == 2
        assert set(candidates) == {'Alice', 'Bob'}
        
        assert ballots[0] == ['Alice', 'Bob']
        assert ballots[1] == ['Bob', 'Alice']
    
    def test_extract_ballots_empty_dataframe(self) -> None:
        """Test ballot extraction from empty DataFrame."""
        df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            extract_ballots_from_dataframe(df)
    
    def test_extract_ballots_no_valid_columns(self) -> None:
        """Test ballot extraction with no valid ranking columns."""
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob'],
            'Age': [25, 30]
        })
        
        with pytest.raises(ValueError):
            extract_ballots_from_dataframe(df)


class TestErrorHandling:
    """Test error handling in file utilities."""
    
    def test_create_template_with_empty_candidates(self) -> None:
        """Test template creation with empty candidates list."""
        with pytest.raises(ValueError):
            create_ballot_template_csv([], num_sample_ballots=5)
        
        with pytest.raises(ValueError):
            create_ballot_template_excel([], num_sample_ballots=5)
    
    def test_export_results_invalid_election(self) -> None:
        """Test results export with invalid election result."""
        # Create election result with inconsistent data
        candidates = [
            CandidateInfo(name="Alice", first_choice_votes=100)
        ]
        
        rounds = []  # Empty rounds - invalid
        
        election_result = ElectionResult(
            winner="Alice",
            total_rounds=0,  # Inconsistent with empty rounds
            candidates=candidates,
            rounds=rounds,
            total_ballots=100
        )
        
        # Should handle gracefully or raise appropriate error
        with pytest.raises(ValueError):
            export_results_to_csv(election_result)
    
    def test_comprehensive_export_error_handling(self) -> None:
        """Test that comprehensive export handles errors gracefully."""
        # Create minimal valid election result
        candidates = [CandidateInfo(name="Alice", first_choice_votes=100, is_winner=True)]
        rounds = [RoundResult(
            round_number=1,
            vote_counts={"Alice": 100},
            eliminated_candidate=None,
            winner="Alice",
            total_votes=100
        )]
        
        election_result = ElectionResult(
            winner="Alice",
            total_rounds=1,
            candidates=candidates,
            rounds=rounds,
            total_ballots=100
        )
        
        # Should create ZIP even with minimal data
        zip_bytes = create_comprehensive_export_zip(election_result, charts_data={})
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_candidate_template(self) -> None:
        """Test template generation with single candidate."""
        candidates = ["Only Candidate"]
        
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=3)
        csv_str = csv_bytes.decode('utf-8')
        
        # Should have one choice column
        assert "Choice 1" in csv_str
        assert "Choice 2" not in csv_str
        
        # Should contain the candidate name
        assert "Only Candidate" in csv_str
    
    def test_very_long_candidate_names(self) -> None:
        """Test handling of very long candidate names."""
        candidates = [
            "This Is A Very Long Candidate Name That Might Cause Issues With File Formats",
            "Another Extremely Long Name For A Candidate In This Election"
        ]
        
        # Should not raise errors
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=2)
        excel_bytes = create_ballot_template_excel(candidates, num_sample_ballots=2)
        
        assert len(csv_bytes) > 0
        assert len(excel_bytes) > 0
    
    def test_special_characters_in_names(self) -> None:
        """Test handling of special characters in candidate names."""
        candidates = ["José María", "O'Connor", "Smith-Jones", "李小明"]
        
        # Should handle special characters gracefully
        csv_bytes = create_ballot_template_csv(candidates, num_sample_ballots=2)
        excel_bytes = create_ballot_template_excel(candidates, num_sample_ballots=2)
        
        assert len(csv_bytes) > 0
        assert len(excel_bytes) > 0
        
        # Verify special characters are preserved in CSV
        csv_str = csv_bytes.decode('utf-8')
        for candidate in candidates:
            assert candidate in csv_str