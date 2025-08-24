"""Tests for formatting utility functions.

This module tests the display formatting utilities used throughout the RCV Dashboard
for consistent and professional presentation of data.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.rcv_dashboard.utils.formatting import (
    format_percentage,
    format_vote_count,
    format_ordinal,
    create_candidate_badge,
    format_round_summary,
    create_progress_bar,
    format_file_size,
    truncate_text,
    format_number_with_commas,
    create_status_indicator,
)


class TestPercentageFormatting:
    """Test percentage formatting functions."""
    
    def test_format_percentage_basic(self) -> None:
        """Test basic percentage formatting."""
        assert format_percentage(0.5) == "50.0%"
        assert format_percentage(0.25) == "25.0%"
        assert format_percentage(0.0) == "0.0%"
        assert format_percentage(1.0) == "100.0%"
    
    def test_format_percentage_decimal_places(self) -> None:
        """Test percentage formatting with different decimal places."""
        assert format_percentage(0.12345, decimals=0) == "12%"
        assert format_percentage(0.12345, decimals=1) == "12.3%"
        assert format_percentage(0.12345, decimals=2) == "12.35%"
        assert format_percentage(0.12345, decimals=3) == "12.345%"
    
    def test_format_percentage_edge_cases(self) -> None:
        """Test percentage formatting edge cases."""
        # Very small numbers
        assert format_percentage(0.001, decimals=1) == "0.1%"
        assert format_percentage(0.001, decimals=3) == "0.100%"
        
        # Numbers greater than 1 (over 100%)
        assert format_percentage(1.5, decimals=1) == "150.0%"
        assert format_percentage(2.0, decimals=0) == "200%"
    
    @given(
        value=st.floats(min_value=0, max_value=5, allow_nan=False, allow_infinity=False),
        decimals=st.integers(min_value=0, max_value=5)
    )
    def test_format_percentage_property_based(self, value: float, decimals: int) -> None:
        """Property-based test for percentage formatting."""
        result = format_percentage(value, decimals)
        
        # Should always end with %
        assert result.endswith("%")
        
        # Should contain a number
        numeric_part = result[:-1]
        try:
            float(numeric_part)
        except ValueError:
            pytest.fail(f"Invalid percentage format: {result}")
    
    def test_format_percentage_negative(self) -> None:
        """Test percentage formatting with negative values."""
        assert format_percentage(-0.1, decimals=1) == "-10.0%"
        assert format_percentage(-0.5, decimals=0) == "-50%"


class TestVoteCountFormatting:
    """Test vote count formatting functions."""
    
    def test_format_vote_count_basic(self) -> None:
        """Test basic vote count formatting."""
        assert format_vote_count(100, 300) == "100 (33.3%)"
        assert format_vote_count(150, 300) == "150 (50.0%)"
        assert format_vote_count(0, 300) == "0 (0.0%)"
        assert format_vote_count(300, 300) == "300 (100.0%)"
    
    def test_format_vote_count_with_decimals(self) -> None:
        """Test vote count formatting with custom decimal places."""
        assert format_vote_count(100, 300, decimals=0) == "100 (33%)"
        assert format_vote_count(100, 300, decimals=2) == "100 (33.33%)"
        assert format_vote_count(100, 300, decimals=3) == "100 (33.333%)"
    
    def test_format_vote_count_edge_cases(self) -> None:
        """Test vote count formatting edge cases."""
        # Zero total votes
        with pytest.raises(ValueError):
            format_vote_count(50, 0)
        
        # Votes exceed total
        assert format_vote_count(350, 300) == "350 (116.7%)"
        
        # Both zero
        with pytest.raises(ValueError):
            format_vote_count(0, 0)
    
    def test_format_vote_count_large_numbers(self) -> None:
        """Test vote count formatting with large numbers."""
        assert format_vote_count(10000, 25000) == "10,000 (40.0%)"
        assert format_vote_count(1000000, 2000000) == "1,000,000 (50.0%)"


class TestOrdinalFormatting:
    """Test ordinal number formatting functions."""
    
    def test_format_ordinal_basic(self) -> None:
        """Test basic ordinal formatting."""
        assert format_ordinal(1) == "1st"
        assert format_ordinal(2) == "2nd"
        assert format_ordinal(3) == "3rd"
        assert format_ordinal(4) == "4th"
        assert format_ordinal(5) == "5th"
    
    def test_format_ordinal_teens(self) -> None:
        """Test ordinal formatting for teen numbers."""
        assert format_ordinal(11) == "11th"
        assert format_ordinal(12) == "12th"
        assert format_ordinal(13) == "13th"
        assert format_ordinal(14) == "14th"
    
    def test_format_ordinal_larger_numbers(self) -> None:
        """Test ordinal formatting for larger numbers."""
        assert format_ordinal(21) == "21st"
        assert format_ordinal(22) == "22nd"
        assert format_ordinal(23) == "23rd"
        assert format_ordinal(24) == "24th"
        
        assert format_ordinal(101) == "101st"
        assert format_ordinal(102) == "102nd"
        assert format_ordinal(103) == "103rd"
        assert format_ordinal(111) == "111th"
        assert format_ordinal(112) == "112th"
    
    @given(n=st.integers(min_value=1, max_value=1000))
    def test_format_ordinal_property_based(self, n: int) -> None:
        """Property-based test for ordinal formatting."""
        result = format_ordinal(n)
        
        # Should start with the number
        assert result.startswith(str(n))
        
        # Should end with st, nd, rd, or th
        suffix = result[len(str(n)):]
        assert suffix in ["st", "nd", "rd", "th"]
    
    def test_format_ordinal_zero_negative(self) -> None:
        """Test ordinal formatting for zero and negative numbers."""
        with pytest.raises(ValueError):
            format_ordinal(0)
        
        with pytest.raises(ValueError):
            format_ordinal(-1)


class TestCandidateBadge:
    """Test candidate badge creation functions."""
    
    def test_create_candidate_badge_basic(self) -> None:
        """Test basic candidate badge creation."""
        badge = create_candidate_badge("Alice Johnson")
        
        assert isinstance(badge, str)
        assert "Alice Johnson" in badge
        assert "span" in badge.lower() or "div" in badge.lower()
    
    def test_create_candidate_badge_with_status(self) -> None:
        """Test candidate badge creation with status."""
        winner_badge = create_candidate_badge("Alice Johnson", status="winner")
        eliminated_badge = create_candidate_badge("Bob Smith", status="eliminated")
        active_badge = create_candidate_badge("Charlie Brown", status="active")
        
        assert "Alice Johnson" in winner_badge
        assert "Bob Smith" in eliminated_badge  
        assert "Charlie Brown" in active_badge
        
        # Different statuses should produce different styling
        assert winner_badge != eliminated_badge
        assert winner_badge != active_badge
    
    def test_create_candidate_badge_with_extra_info(self) -> None:
        """Test candidate badge creation with extra information."""
        badge = create_candidate_badge(
            "Alice Johnson", 
            status="winner", 
            extra_info="150 votes (50.0%)"
        )
        
        assert "Alice Johnson" in badge
        assert "150 votes" in badge
        assert "50.0%" in badge
    
    def test_create_candidate_badge_special_characters(self) -> None:
        """Test candidate badge with special characters in names."""
        badge = create_candidate_badge("José O'Connor-Smith", status="active")
        
        assert "José O'Connor-Smith" in badge
        # Should handle special characters without errors


class TestRoundSummary:
    """Test round summary formatting functions."""
    
    def test_format_round_summary_basic(self) -> None:
        """Test basic round summary formatting."""
        vote_counts = {"Alice": 120, "Bob": 100, "Charlie": 80}
        summary = format_round_summary(
            round_number=1,
            vote_counts=vote_counts,
            eliminated_candidate="Charlie",
            winner=None
        )
        
        assert isinstance(summary, str)
        assert "Round 1" in summary
        assert "Alice" in summary
        assert "Bob" in summary
        assert "Charlie" in summary
        assert "eliminated" in summary.lower()
    
    def test_format_round_summary_final_round(self) -> None:
        """Test round summary formatting for final round."""
        vote_counts = {"Alice": 180, "Bob": 120}
        summary = format_round_summary(
            round_number=2,
            vote_counts=vote_counts,
            eliminated_candidate="Bob",
            winner="Alice"
        )
        
        assert "Round 2" in summary
        assert "Alice" in summary
        assert "winner" in summary.lower() or "wins" in summary.lower()
    
    def test_format_round_summary_first_round_majority(self) -> None:
        """Test round summary for first-round majority winner."""
        vote_counts = {"Alice": 200, "Bob": 50, "Charlie": 50}
        summary = format_round_summary(
            round_number=1,
            vote_counts=vote_counts,
            eliminated_candidate=None,
            winner="Alice"
        )
        
        assert "Round 1" in summary
        assert "Alice" in summary
        assert "majority" in summary.lower() or "winner" in summary.lower()


class TestProgressBar:
    """Test progress bar creation functions."""
    
    def test_create_progress_bar_basic(self) -> None:
        """Test basic progress bar creation."""
        progress_bar = create_progress_bar(50, 100)
        
        assert isinstance(progress_bar, str)
        assert "50" in progress_bar or "50%" in progress_bar
        # Should contain some form of visual indicator
        assert len(progress_bar) > 10
    
    def test_create_progress_bar_edge_cases(self) -> None:
        """Test progress bar creation edge cases."""
        # 0% progress
        zero_bar = create_progress_bar(0, 100)
        assert isinstance(zero_bar, str)
        
        # 100% progress
        full_bar = create_progress_bar(100, 100)
        assert isinstance(full_bar, str)
        
        # Over 100%
        over_bar = create_progress_bar(120, 100)
        assert isinstance(over_bar, str)
    
    def test_create_progress_bar_with_color(self) -> None:
        """Test progress bar creation with color."""
        colored_bar = create_progress_bar(75, 100, color="blue")
        
        assert isinstance(colored_bar, str)
        assert "blue" in colored_bar or "75" in colored_bar


class TestFileSizeFormatting:
    """Test file size formatting functions."""
    
    def test_format_file_size_bytes(self) -> None:
        """Test file size formatting for bytes."""
        assert format_file_size(512) == "512 B"
        assert format_file_size(1000) == "1000 B"
    
    def test_format_file_size_kilobytes(self) -> None:
        """Test file size formatting for kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(2048) == "2.0 KB"
        assert format_file_size(1536) == "1.5 KB"
    
    def test_format_file_size_megabytes(self) -> None:
        """Test file size formatting for megabytes."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 2.5) == "2.5 MB"
    
    def test_format_file_size_gigabytes(self) -> None:
        """Test file size formatting for gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1024 * 1024 * 1024 * 1.5) == "1.5 GB"
    
    def test_format_file_size_zero(self) -> None:
        """Test file size formatting for zero bytes."""
        assert format_file_size(0) == "0 B"
    
    @given(size=st.integers(min_value=0, max_value=10**12))
    def test_format_file_size_property_based(self, size: int) -> None:
        """Property-based test for file size formatting."""
        result = format_file_size(size)
        
        # Should contain a number and a unit
        parts = result.split()
        assert len(parts) == 2
        
        # First part should be a number
        try:
            float(parts[0])
        except ValueError:
            pytest.fail(f"Invalid file size format: {result}")
        
        # Second part should be a valid unit
        assert parts[1] in ["B", "KB", "MB", "GB", "TB"]


class TestTextTruncation:
    """Test text truncation functions."""
    
    def test_truncate_text_basic(self) -> None:
        """Test basic text truncation."""
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_text(long_text, max_length=20)
        
        assert len(truncated) <= 23  # 20 + "..."
        assert truncated.endswith("...")
        assert truncated.startswith("This is a very")
    
    def test_truncate_text_no_truncation_needed(self) -> None:
        """Test text truncation when no truncation is needed."""
        short_text = "Short text"
        truncated = truncate_text(short_text, max_length=20)
        
        assert truncated == short_text
        assert not truncated.endswith("...")
    
    def test_truncate_text_exact_length(self) -> None:
        """Test text truncation at exact max length."""
        text = "Exact length text"
        truncated = truncate_text(text, max_length=17)
        
        assert truncated == text
        assert not truncated.endswith("...")
    
    def test_truncate_text_custom_suffix(self) -> None:
        """Test text truncation with custom suffix."""
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_text(long_text, max_length=20, suffix="…")
        
        assert truncated.endswith("…")
        assert len(truncated) <= 21  # 20 + "…"
    
    def test_truncate_text_very_short_max_length(self) -> None:
        """Test text truncation with very short max length."""
        text = "Long text"
        truncated = truncate_text(text, max_length=5)
        
        assert len(truncated) <= 8  # 5 + "..."
        assert truncated.endswith("...")


class TestNumberFormatting:
    """Test number formatting with commas."""
    
    def test_format_number_with_commas_basic(self) -> None:
        """Test basic number formatting with commas."""
        assert format_number_with_commas(1000) == "1,000"
        assert format_number_with_commas(1000000) == "1,000,000"
        assert format_number_with_commas(12345) == "12,345"
        assert format_number_with_commas(123456789) == "123,456,789"
    
    def test_format_number_with_commas_small_numbers(self) -> None:
        """Test number formatting for small numbers."""
        assert format_number_with_commas(0) == "0"
        assert format_number_with_commas(1) == "1"
        assert format_number_with_commas(12) == "12"
        assert format_number_with_commas(123) == "123"
        assert format_number_with_commas(999) == "999"
    
    def test_format_number_with_commas_negative(self) -> None:
        """Test number formatting for negative numbers."""
        assert format_number_with_commas(-1000) == "-1,000"
        assert format_number_with_commas(-1234567) == "-1,234,567"
    
    @given(n=st.integers(min_value=-10**9, max_value=10**9))
    def test_format_number_with_commas_property_based(self, n: int) -> None:
        """Property-based test for number formatting."""
        result = format_number_with_commas(n)
        
        # Remove commas and check it's still the original number
        cleaned = result.replace(",", "")
        assert int(cleaned) == n


class TestStatusIndicator:
    """Test status indicator creation functions."""
    
    def test_create_status_indicator_success(self) -> None:
        """Test status indicator creation for success status."""
        indicator = create_status_indicator("success", "Election completed")
        
        assert isinstance(indicator, str)
        assert "success" in indicator.lower() or "✓" in indicator or "✅" in indicator
        assert "Election completed" in indicator
    
    def test_create_status_indicator_error(self) -> None:
        """Test status indicator creation for error status."""
        indicator = create_status_indicator("error", "Invalid ballot data")
        
        assert isinstance(indicator, str)
        assert "error" in indicator.lower() or "✗" in indicator or "❌" in indicator
        assert "Invalid ballot data" in indicator
    
    def test_create_status_indicator_warning(self) -> None:
        """Test status indicator creation for warning status."""
        indicator = create_status_indicator("warning", "Large file upload")
        
        assert isinstance(indicator, str)
        assert "warning" in indicator.lower() or "⚠" in indicator or "⚠️" in indicator
        assert "Large file upload" in indicator
    
    def test_create_status_indicator_info(self) -> None:
        """Test status indicator creation for info status."""
        indicator = create_status_indicator("info", "Processing ballots")
        
        assert isinstance(indicator, str)
        assert "info" in indicator.lower() or "ℹ" in indicator or "ℹ️" in indicator
        assert "Processing ballots" in indicator


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in formatting functions."""
    
    def test_format_percentage_invalid_input(self) -> None:
        """Test percentage formatting with invalid input."""
        with pytest.raises(TypeError):
            format_percentage("not a number")  # type: ignore
        
        with pytest.raises(ValueError):
            format_percentage(0.5, decimals=-1)
    
    def test_format_vote_count_invalid_input(self) -> None:
        """Test vote count formatting with invalid input."""
        with pytest.raises(TypeError):
            format_vote_count("100", 300)  # type: ignore
        
        with pytest.raises(ValueError):
            format_vote_count(100, 0)  # Division by zero
        
        with pytest.raises(ValueError):
            format_vote_count(-50, 100)  # Negative votes
    
    def test_create_candidate_badge_empty_name(self) -> None:
        """Test candidate badge creation with empty name."""
        badge = create_candidate_badge("")
        assert isinstance(badge, str)
        # Should handle gracefully, possibly with placeholder
    
    def test_truncate_text_invalid_input(self) -> None:
        """Test text truncation with invalid input."""
        with pytest.raises(ValueError):
            truncate_text("text", max_length=0)
        
        with pytest.raises(ValueError):
            truncate_text("text", max_length=-5)
    
    def test_format_file_size_negative(self) -> None:
        """Test file size formatting with negative input."""
        with pytest.raises(ValueError):
            format_file_size(-100)