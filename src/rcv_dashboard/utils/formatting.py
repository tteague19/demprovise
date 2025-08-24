"""Display formatting utilities for RCV Dashboard.

This module provides consistent formatting functions for percentages,
vote counts, candidate displays, and other UI elements throughout the application.
"""

from __future__ import annotations

import html
from typing import Any


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a percentage value with consistent rounding and display.
    
    Args:
        value: Percentage value (0-100 range)
        decimals: Number of decimal places to display
        
    Returns:
        Formatted percentage string with % symbol
        
    Example:
        >>> format_percentage(45.678, 1)
        '45.7%'
        >>> format_percentage(100.0, 0)
        '100%'
    """
    if not isinstance(value, (int, float)):
        return "0.0%"
    
    if value < 0:
        return "0.0%"
    
    if value > 100:
        return "100.0%"
    
    return f"{value:.{decimals}f}%"


def format_vote_count(count: int, total: int | None = None) -> str:
    """Format vote count with optional percentage of total.
    
    Args:
        count: Number of votes
        total: Total votes for percentage calculation (optional)
        
    Returns:
        Formatted string with vote count and optional percentage
        
    Example:
        >>> format_vote_count(150, 500)
        '150 (30.0%)'
        >>> format_vote_count(75)
        '75'
    """
    if not isinstance(count, int) or count < 0:
        count = 0
    
    formatted_count = f"{count:,}"
    
    if total is not None and isinstance(total, int) and total > 0:
        percentage = (count / total) * 100
        return f"{formatted_count} ({format_percentage(percentage)})"
    
    return formatted_count


def format_candidate_name(name: str, max_length: int = 25) -> str:
    """Format candidate name for display with length limits.
    
    Args:
        name: Candidate name to format
        max_length: Maximum display length before truncation
        
    Returns:
        Formatted candidate name, truncated with ellipsis if needed
        
    Example:
        >>> format_candidate_name("Very Long Candidate Name Here", 15)
        'Very Long Can...'
        >>> format_candidate_name("Bob Smith", 15)
        'Bob Smith'
    """
    if not isinstance(name, str):
        name = str(name)
    
    name = name.strip()
    
    if len(name) <= max_length:
        return name
    
    return name[:max_length-3] + "..."


def create_candidate_badge(
    name: str, 
    status: str = "active", 
    extra_info: str = ""
) -> str:
    """Create an HTML badge for candidate display with status styling.
    
    Args:
        name: Candidate name
        status: Candidate status (winner, eliminated, active)
        extra_info: Additional information to display
        
    Returns:
        HTML string with styled candidate badge
        
    Example:
        >>> badge = create_candidate_badge("Alice", "winner", "Round 3")
        >>> st.markdown(badge, unsafe_allow_html=True)
    """
    # Escape HTML characters in name and info
    safe_name = html.escape(name)
    safe_info = html.escape(extra_info) if extra_info else ""
    
    # Define status colors and symbols
    status_configs = {
        "winner": {"color": "#28a745", "bg": "#d4edda", "symbol": "🏆"},
        "eliminated": {"color": "#dc3545", "bg": "#f8d7da", "symbol": "❌"},
        "active": {"color": "#007bff", "bg": "#d1ecf1", "symbol": "▶️"},
        "default": {"color": "#6c757d", "bg": "#e2e3e5", "symbol": "•"}
    }
    
    config = status_configs.get(status.lower(), status_configs["default"])
    
    # Build the badge HTML
    badge_parts = [f"{config['symbol']} {safe_name}"]
    if safe_info:
        badge_parts.append(f"<small>({safe_info})</small>")
    
    badge_content = " ".join(badge_parts)
    
    return f"""
    <span style="
        display: inline-block;
        padding: 0.25em 0.6em;
        margin: 0.1em;
        font-size: 0.875em;
        font-weight: 500;
        line-height: 1;
        color: {config['color']};
        background-color: {config['bg']};
        border: 1px solid {config['color']};
        border-radius: 0.375rem;
        white-space: nowrap;
    ">{badge_content}</span>
    """


def format_round_header(round_number: int, is_final: bool = False) -> str:
    """Format a round header with appropriate styling and context.
    
    Args:
        round_number: The round number (1-based)
        is_final: Whether this is the final/winning round
        
    Returns:
        Formatted round header string
        
    Example:
        >>> format_round_header(1, False)
        '🗳️ Round 1'
        >>> format_round_header(3, True)
        '🏆 Final Round (Round 3)'
    """
    if not isinstance(round_number, int) or round_number < 1:
        return "Round ?"
    
    if is_final:
        return f"🏆 Final Round (Round {round_number})"
    else:
        return f"🗳️ Round {round_number}"


def format_elimination_message(candidate: str, round_number: int) -> str:
    """Format an elimination message with appropriate styling.
    
    Args:
        candidate: Name of eliminated candidate
        round_number: Round in which elimination occurred
        
    Returns:
        Formatted elimination message
        
    Example:
        >>> format_elimination_message("Bob Smith", 2)
        '❌ Bob Smith eliminated in Round 2'
    """
    safe_candidate = html.escape(candidate)
    return f"❌ {safe_candidate} eliminated in Round {round_number}"


def format_winner_announcement(candidate: str, percentage: float) -> str:
    """Format a winner announcement with celebration styling.
    
    Args:
        candidate: Name of winning candidate
        percentage: Final vote percentage
        
    Returns:
        Formatted winner announcement
        
    Example:
        >>> format_winner_announcement("Alice Johnson", 67.5)
        '🎉 Alice Johnson wins with 67.5%! 🎉'
    """
    safe_candidate = html.escape(candidate)
    formatted_pct = format_percentage(percentage)
    return f"🎉 {safe_candidate} wins with {formatted_pct}! 🎉"


def format_vote_transfer(
    from_candidate: str, 
    to_candidate: str, 
    vote_count: int
) -> str:
    """Format a vote transfer description.
    
    Args:
        from_candidate: Candidate losing votes
        to_candidate: Candidate receiving votes  
        vote_count: Number of votes transferred
        
    Returns:
        Formatted transfer description
        
    Example:
        >>> format_vote_transfer("Bob", "Alice", 25)
        '25 votes: Bob → Alice'
    """
    safe_from = html.escape(from_candidate)
    safe_to = html.escape(to_candidate)
    formatted_count = format_vote_count(vote_count)
    
    return f"{formatted_count} votes: {safe_from} → {safe_to}"


def format_ballot_summary(
    total_ballots: int, 
    valid_ballots: int, 
    invalid_ballots: int = 0
) -> str:
    """Format a ballot summary with counts and validity.
    
    Args:
        total_ballots: Total number of ballots
        valid_ballots: Number of valid ballots processed
        invalid_ballots: Number of invalid/excluded ballots
        
    Returns:
        Formatted ballot summary string
        
    Example:
        >>> format_ballot_summary(105, 100, 5)
        '105 total ballots: 100 valid (95.2%), 5 invalid (4.8%)'
    """
    if total_ballots <= 0:
        return "No ballots available"
    
    total_fmt = f"{total_ballots:,}"
    valid_fmt = f"{valid_ballots:,}"
    invalid_fmt = f"{invalid_ballots:,}"
    
    valid_pct = format_percentage((valid_ballots / total_ballots) * 100)
    
    if invalid_ballots > 0:
        invalid_pct = format_percentage((invalid_ballots / total_ballots) * 100)
        return f"{total_fmt} total ballots: {valid_fmt} valid ({valid_pct}), {invalid_fmt} invalid ({invalid_pct})"
    else:
        return f"{total_fmt} ballots: all valid ({valid_pct})"


def format_majority_threshold(threshold: int, total_ballots: int) -> str:
    """Format majority threshold information.
    
    Args:
        threshold: Number of votes needed for majority
        total_ballots: Total ballots cast
        
    Returns:
        Formatted threshold description
        
    Example:
        >>> format_majority_threshold(126, 250)
        'Majority threshold: 126 votes (50.4% of 250 ballots)'
    """
    threshold_fmt = f"{threshold:,}"
    total_fmt = f"{total_ballots:,}"
    
    if total_ballots > 0:
        percentage = (threshold / total_ballots) * 100
        pct_fmt = format_percentage(percentage)
        return f"Majority threshold: {threshold_fmt} votes ({pct_fmt} of {total_fmt} ballots)"
    else:
        return f"Majority threshold: {threshold_fmt} votes"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
        
    Example:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(2048576)
        '2.0 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 50, ellipsis: str = "...") -> str:
    """Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        ellipsis: String to append when truncating
        
    Returns:
        Truncated text with ellipsis if needed
        
    Example:
        >>> truncate_text("This is a very long text string", 20)
        'This is a very lo...'
    """
    if not isinstance(text, str):
        text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(ellipsis)] + ellipsis


def format_round_summary(round_number: int, round_result: Any, 
                        is_final: bool = False, has_majority: bool = False) -> str:
    """Create a formatted summary of an election round.
    
    Args:
        round_number: Round number (1-based)
        round_result: RoundResult object with vote counts and elimination info
        is_final: Whether this is the final round
        has_majority: Whether someone achieved majority in this round
        
    Returns:
        Formatted HTML string summarizing the round
        
    Examples:
        >>> from types import SimpleNamespace
        >>> round_result = SimpleNamespace(
        ...     vote_counts={"Alice": 150, "Bob": 100}, 
        ...     eliminated_candidate="Bob",
        ...     total_votes=250
        ... )
        >>> summary = format_round_summary(2, round_result, is_final=False, has_majority=False)
        >>> "Round 2" in summary
        True
        >>> "Bob" in summary
        True
    """
    vote_counts = getattr(round_result, 'vote_counts', {})
    eliminated = getattr(round_result, 'eliminated_candidate', None)
    total_votes = getattr(round_result, 'total_votes', 0)
    
    lines = [f"<div class='round-summary'><strong>Round {round_number}</strong>"]
    
    if vote_counts:
        # Sort candidates by vote count
        sorted_candidates = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        
        for candidate, votes in sorted_candidates:
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            status = ""
            if has_majority and candidate == sorted_candidates[0][0]:
                status = " <span class='winner'>🏆 Winner</span>"
            elif eliminated and candidate == eliminated:
                status = " <span class='eliminated'>❌ Eliminated</span>"
            
            lines.append(f"• {candidate}: {votes:,} votes ({percentage:.1f}%){status}")
    
    if eliminated and not is_final:
        lines.append(f"<em>{eliminated} eliminated (lowest votes)</em>")
    elif is_final:
        lines.append("<em>Election complete!</em>")
    
    lines.append("</div>")
    return "<br>".join(lines)


def format_number_with_commas(number: int) -> str:
    """Format integer with comma separators for thousands.
    
    Args:
        number: Integer to format
        
    Returns:
        Formatted number string with commas
        
    Examples:
        >>> format_number_with_commas(1000)
        '1,000'
        >>> format_number_with_commas(1234567)
        '1,234,567'
        >>> format_number_with_commas(123)
        '123'
    """
    return f"{number:,}"


def create_status_indicator(status: str, label: str = "") -> str:
    """Create a colored status indicator for UI display.
    
    Args:
        status: Status type ('active', 'eliminated', 'winner', etc.)
        label: Optional label text to display
        
    Returns:
        HTML string with colored status indicator
        
    Examples:
        >>> indicator = create_status_indicator("winner", "Alice")
        >>> "winner" in indicator.lower()
        True
        >>> "Alice" in indicator
        True
    """
    status_colors = {
        "active": "#28a745",      # Green
        "eliminated": "#dc3545",  # Red  
        "winner": "#ffc107",      # Gold
        "pending": "#6c757d",     # Gray
        "leading": "#007bff",     # Blue
    }
    
    color = status_colors.get(status.lower(), "#6c757d")
    display_text = label if label else status.title()
    
    return f'<span style="color: {color}; font-weight: bold;">● {display_text}</span>'


def format_ordinal(number: int) -> str:
    """Format number with ordinal suffix (1st, 2nd, 3rd, etc.).
    
    Args:
        number: Number to format
        
    Returns:
        Number with appropriate ordinal suffix
        
    Example:
        >>> format_ordinal(1)
        '1st'
        >>> format_ordinal(23)
        '23rd'
    """
    if not isinstance(number, int) or number < 1:
        return str(number)
    
    # Handle special cases for 11th, 12th, 13th
    if 10 <= number % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    
    return f"{number}{suffix}"


def create_progress_bar(
    current: int, 
    total: int, 
    width: int = 20, 
    filled_char: str = "█", 
    empty_char: str = "░"
) -> str:
    """Create a text-based progress bar.
    
    Args:
        current: Current progress value
        total: Total/maximum value
        width: Width of progress bar in characters
        filled_char: Character for filled portions
        empty_char: Character for empty portions
        
    Returns:
        Text progress bar with percentage
        
    Example:
        >>> create_progress_bar(7, 10, 10)
        '███████░░░ 70.0%'
    """
    if total <= 0:
        return f"{empty_char * width} 0.0%"
    
    progress = min(current / total, 1.0)
    filled_length = int(width * progress)
    empty_length = width - filled_length
    
    bar = filled_char * filled_length + empty_char * empty_length
    percentage = format_percentage(progress * 100)
    
    return f"{bar} {percentage}"