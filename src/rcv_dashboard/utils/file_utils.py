"""File utility functions for template generation and data export.

This module provides functionality for generating ballot templates,
exporting election results, and handling file downloads in the Streamlit app.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

from ..core.models import ElectionResult


def create_ballot_template_csv(
    candidates: Sequence[str], 
    num_sample_ballots: int = 10
) -> bytes:
    """Create a CSV ballot template with sample data.
    
    Generates a downloadable CSV file that users can use as a template
    for creating their own ballot data files.
    
    Args:
        candidates: List of candidate names to include
        num_sample_ballots: Number of sample ballot rows to generate
        
    Returns:
        CSV file content as bytes
        
    Example:
        >>> candidates = ["Alice", "Bob", "Charlie"]
        >>> csv_data = create_ballot_template_csv(candidates, 5)
        >>> st.download_button("Download Template", csv_data, "template.csv")
    """
    if not candidates:
        raise ValueError("At least one candidate is required")
    
    if num_sample_ballots < 1:
        raise ValueError("Number of sample ballots must be positive")
    
    # Create column headers
    max_choices = len(candidates)
    columns = [f"Choice {i+1}" for i in range(max_choices)]
    
    # Generate sample ballot data with different voting patterns
    sample_data = []
    candidate_list = list(candidates)
    
    for i in range(num_sample_ballots):
        ballot_row = {}
        
        if i < len(candidate_list):
            # First few ballots: each candidate gets a first-place vote
            primary_choice = candidate_list[i]
            remaining = [c for c in candidate_list if c != primary_choice]
            
            ballot_row[columns[0]] = primary_choice
            for j, candidate in enumerate(remaining[:max_choices-1]):
                ballot_row[columns[j+1]] = candidate
        else:
            # Additional ballots: create varied voting patterns
            import random
            shuffled = candidate_list.copy()
            random.Random(i).shuffle(shuffled)  # Deterministic shuffle for consistency
            
            for j, candidate in enumerate(shuffled[:max_choices]):
                ballot_row[columns[j]] = candidate
        
        # Fill empty columns with empty strings
        for col in columns:
            if col not in ballot_row:
                ballot_row[col] = ""
        
        sample_data.append(ballot_row)
    
    # Create DataFrame and convert to CSV
    df = pd.DataFrame(sample_data)
    
    # Add a header row with instructions
    instruction_row = {
        columns[0]: "# Instructions: Replace these sample ballots with your actual voting data",
        **{col: "" for col in columns[1:]}
    }
    
    # Create final DataFrame with instructions
    df_with_instructions = pd.DataFrame([instruction_row] + df.to_dict('records'))
    
    # Convert to CSV bytes
    csv_buffer = io.StringIO()
    df_with_instructions.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode('utf-8')


def create_ballot_template_excel(
    candidates: Sequence[str], 
    num_sample_ballots: int = 10
) -> bytes:
    """Create an Excel ballot template with sample data and formatting.
    
    Generates a professionally formatted Excel file that users can use
    as a template, with proper styling and data validation.
    
    Args:
        candidates: List of candidate names to include
        num_sample_ballots: Number of sample ballot rows to generate
        
    Returns:
        Excel file content as bytes
        
    Example:
        >>> candidates = ["Alice", "Bob", "Charlie"]
        >>> excel_data = create_ballot_template_excel(candidates)
        >>> st.download_button("Download Template", excel_data, "template.xlsx")
    """
    if not candidates:
        raise ValueError("At least one candidate is required")
    
    if num_sample_ballots < 1:
        raise ValueError("Number of sample ballots must be positive")
    
    # Create workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Ballot Data"
    
    # Create column headers
    max_choices = len(candidates)
    columns = [f"Choice {i+1}" for i in range(max_choices)]
    
    # Add title and instructions
    ws['A1'] = "RCV Ballot Template"
    ws['A1'].font = Font(size=16, bold=True)
    
    ws['A3'] = "Instructions:"
    ws['A3'].font = Font(bold=True)
    ws['A4'] = "1. Replace the sample data below with your actual ballot data"
    ws['A5'] = "2. Each row represents one voter's ranked preferences"
    ws['A6'] = "3. Leave cells blank for unranked candidates"
    ws['A7'] = f"4. Available candidates: {', '.join(candidates)}"
    
    # Add headers starting at row 9
    header_row = 9
    for col_idx, header in enumerate(columns, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    # Generate sample data (same logic as CSV version)
    sample_data = []
    candidate_list = list(candidates)
    
    for i in range(num_sample_ballots):
        ballot_row = {}
        
        if i < len(candidate_list):
            primary_choice = candidate_list[i]
            remaining = [c for c in candidate_list if c != primary_choice]
            
            ballot_row[columns[0]] = primary_choice
            for j, candidate in enumerate(remaining[:max_choices-1]):
                ballot_row[columns[j+1]] = candidate
        else:
            import random
            shuffled = candidate_list.copy()
            random.Random(i).shuffle(shuffled)
            
            for j, candidate in enumerate(shuffled[:max_choices]):
                ballot_row[columns[j]] = candidate
        
        sample_data.append(ballot_row)
    
    # Add sample data starting at row 10
    data_start_row = 10
    for row_idx, ballot in enumerate(sample_data):
        for col_idx, header in enumerate(columns, 1):
            value = ballot.get(header, "")
            ws.cell(row=data_start_row + row_idx, column=col_idx, value=value)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Add candidate list worksheet
    candidates_ws = wb.create_sheet("Candidate List")
    candidates_ws['A1'] = "Available Candidates"
    candidates_ws['A1'].font = Font(size=14, bold=True)
    
    for i, candidate in enumerate(candidates, 2):
        candidates_ws[f'A{i}'] = candidate
    
    # Save to bytes buffer
    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


def export_results_to_csv(election_result: ElectionResult) -> bytes:
    """Export complete election results to a comprehensive CSV file.
    
    Creates a detailed CSV export including round-by-round results,
    candidate information, and vote transfer details.
    
    Args:
        election_result: Complete election results to export
        
    Returns:
        CSV file content as bytes containing all election data
        
    Example:
        >>> csv_data = export_results_to_csv(election_result)
        >>> st.download_button("Download Results", csv_data, "election_results.csv")
    """
    # Create multiple dataframes for different aspects of the results
    export_data = []
    
    # Election summary
    export_data.append("ELECTION SUMMARY")
    export_data.append(f"Winner,{election_result.winner}")
    export_data.append(f"Total Ballots,{election_result.total_ballots}")
    export_data.append(f"Total Rounds,{len(election_result.rounds)}")
    export_data.append(f"Majority Threshold,{election_result.majority_threshold}")
    export_data.append(f"Winner Vote Percentage,{election_result.winner_vote_percentage:.2f}%")
    export_data.append("")
    
    # Candidate information
    export_data.append("CANDIDATE INFORMATION")
    export_data.append("Name,Status,Final Vote Count,Elimination Round")
    
    for candidate in election_result.candidates:
        elimination = candidate.elimination_round or ""
        export_data.append(
            f"{candidate.name},{candidate.status},{candidate.vote_count},{elimination}"
        )
    export_data.append("")
    
    # Round-by-round results
    export_data.append("ROUND BY ROUND RESULTS")
    
    # Create headers
    all_candidates = sorted([c.name for c in election_result.candidates])
    headers = ["Round", "Total Votes", "Exhausted Ballots"] + all_candidates + ["Eliminated"]
    export_data.append(",".join(headers))
    
    # Add data for each round
    for round_result in election_result.rounds:
        row_data = [
            str(round_result.round_number),
            str(round_result.total_votes),
            str(round_result.exhausted_ballots)
        ]
        
        # Add vote counts for each candidate
        for candidate in all_candidates:
            votes = round_result.vote_counts.get(candidate, 0)
            row_data.append(str(votes))
        
        # Add elimination info
        eliminated = round_result.eliminated_candidate or ""
        row_data.append(eliminated)
        
        export_data.append(",".join(row_data))
    
    export_data.append("")
    
    # Vote transfer details
    export_data.append("VOTE TRANSFERS")
    export_data.append("Round,From Candidate,To Candidate,Vote Count")
    
    for round_result in election_result.rounds:
        if round_result.vote_transfers:
            for transfer in round_result.vote_transfers:
                export_data.append(
                    f"{transfer.transfer_round},{transfer.from_candidate},"
                    f"{transfer.to_candidate},{transfer.vote_count}"
                )
    
    # Join all data and convert to bytes
    csv_content = "\n".join(export_data)
    return csv_content.encode('utf-8')


def export_chart_as_image(chart: go.Figure, filename_prefix: str = "rcv_chart") -> bytes:
    """Export a Plotly chart as a PNG image.
    
    Converts a Plotly figure to a high-quality PNG image for download.
    
    Args:
        chart: Plotly figure to export
        filename_prefix: Prefix for the suggested filename
        
    Returns:
        PNG image data as bytes
        
    Note:
        Requires kaleido package for image export. In production environments,
        consider using plotly.io.to_image with proper kaleido setup.
        
    Example:
        >>> fig = create_vote_progression_chart(election_result)
        >>> png_data = export_chart_as_image(fig, "vote_progression")
        >>> st.download_button("Download Chart", png_data, "chart.png")
    """
    try:
        # Try to export as image (requires kaleido)
        img_bytes = chart.to_image(format="png", width=1200, height=800, scale=2)
        return img_bytes
    except Exception:
        # Fallback: export as HTML if image export fails
        html_content = chart.to_html(include_plotlyjs=True)
        return html_content.encode('utf-8')


def create_comprehensive_export_zip(
    election_result: ElectionResult,
    charts: Sequence[go.Figure] | None = None
) -> bytes:
    """Create a comprehensive ZIP export with all election data and visualizations.
    
    Creates a ZIP file containing:
    - Detailed CSV results
    - Chart images (if charts provided)
    - Summary report
    
    Args:
        election_result: Complete election results
        charts: Optional list of charts to include as images
        
    Returns:
        ZIP file content as bytes
        
    Example:
        >>> charts = [vote_chart, sankey_chart, pie_chart]
        >>> zip_data = create_comprehensive_export_zip(election_result, charts)
        >>> st.download_button("Download All", zip_data, "election_export.zip")
    """
    import zipfile
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add CSV results
        csv_data = export_results_to_csv(election_result)
        zip_file.writestr("election_results.csv", csv_data)
        
        # Add charts if provided
        if charts:
            for i, chart in enumerate(charts):
                try:
                    chart_data = export_chart_as_image(chart, f"chart_{i+1}")
                    # Determine file extension based on content
                    if chart_data.startswith(b'<!DOCTYPE html') or chart_data.startswith(b'<html'):
                        filename = f"chart_{i+1}.html"
                    else:
                        filename = f"chart_{i+1}.png"
                    
                    zip_file.writestr(filename, chart_data)
                except Exception as e:
                    # Add error log if chart export fails
                    error_msg = f"Failed to export chart {i+1}: {str(e)}\n"
                    zip_file.writestr(f"chart_{i+1}_error.txt", error_msg.encode('utf-8'))
        
        # Add summary report
        summary_data = _create_summary_report(election_result)
        zip_file.writestr("election_summary.txt", summary_data.encode('utf-8'))
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def _create_summary_report(election_result: ElectionResult) -> str:
    """Create a human-readable summary report of the election results.
    
    Args:
        election_result: Complete election results
        
    Returns:
        Formatted text summary of the election
    """
    lines = [
        "RANKED CHOICE VOTING ELECTION SUMMARY",
        "=" * 50,
        "",
        f"Winner: {election_result.winner}",
        f"Final Vote Percentage: {election_result.winner_vote_percentage:.1f}%",
        f"Total Ballots Cast: {election_result.total_ballots:,}",
        f"Number of Rounds: {len(election_result.rounds)}",
        f"Majority Threshold: {election_result.majority_threshold:,} votes",
        "",
        "ELIMINATION ORDER:",
        "-" * 20
    ]
    
    # Add elimination order
    eliminations = []
    for round_result in election_result.rounds:
        if round_result.eliminated_candidate:
            eliminations.append(
                f"Round {round_result.round_number}: {round_result.eliminated_candidate}"
            )
    
    if eliminations:
        lines.extend(eliminations)
    else:
        lines.append("No eliminations (winner determined in first round)")
    
    lines.extend([
        "",
        "FINAL RESULTS:",
        "-" * 15
    ])
    
    # Sort candidates by final vote count
    sorted_candidates = sorted(
        election_result.candidates, 
        key=lambda c: c.vote_count, 
        reverse=True
    )
    
    for i, candidate in enumerate(sorted_candidates, 1):
        status_symbol = "🏆" if candidate.status == "winner" else f"{i}."
        percentage = (candidate.vote_count / election_result.total_ballots * 100) if election_result.total_ballots > 0 else 0
        lines.append(
            f"{status_symbol} {candidate.name}: {candidate.vote_count:,} votes ({percentage:.1f}%)"
        )
    
    # Add vote transfer summary
    total_transfers = sum(
        len(round_result.vote_transfers) 
        for round_result in election_result.rounds
    )
    
    if total_transfers > 0:
        lines.extend([
            "",
            "VOTE TRANSFER SUMMARY:",
            "-" * 22,
            f"Total transfer events: {total_transfers}",
            ""
        ])
        
        for round_result in election_result.rounds:
            if round_result.vote_transfers:
                lines.append(f"Round {round_result.round_number} transfers from {round_result.eliminated_candidate}:")
                for transfer in round_result.vote_transfers:
                    lines.append(f"  → {transfer.vote_count} votes to {transfer.to_candidate}")
    
    # Add exhausted ballot information
    final_round = election_result.rounds[-1] if election_result.rounds else None
    if final_round and final_round.exhausted_ballots > 0:
        exhausted_pct = (final_round.exhausted_ballots / election_result.total_ballots * 100)
        lines.extend([
            "",
            "BALLOT EXHAUSTION:",
            "-" * 18,
            f"Exhausted ballots: {final_round.exhausted_ballots:,} ({exhausted_pct:.1f}%)"
        ])
    
    lines.extend([
        "",
        "Report generated by RCV Dashboard",
        f"https://github.com/example/demprovise"
    ])
    
    return "\n".join(lines)


def validate_uploaded_file(uploaded_file: Any, max_size_mb: float = 50.0) -> dict[str, Any]:
    """Validate an uploaded file for safety and constraints.
    
    Checks file size, type, and basic safety requirements for uploaded ballot files.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        max_size_mb: Maximum allowed file size in megabytes
        
    Returns:
        Dictionary with validation results:
        - is_valid: bool indicating if file passes validation
        - error_message: str error description if validation fails
        - file_info: dict with file metadata
        
    Examples:
        >>> # Mock file for testing
        >>> import io
        >>> class MockFile:
        ...     def __init__(self, name, content, type_):
        ...         self.name = name
        ...         self._content = content
        ...         self.type = type_
        ...     def getvalue(self):
        ...         return self._content.encode() if isinstance(self._content, str) else self._content
        >>> 
        >>> mock_file = MockFile("test.csv", "header,data\\n", "text/csv")
        >>> result = validate_uploaded_file(mock_file, max_size_mb=10)
        >>> result["is_valid"]
        True
        >>> "file_info" in result
        True
    """
    try:
        if not uploaded_file:
            return {
                "is_valid": False,
                "error_message": "No file uploaded",
                "file_info": {}
            }
        
        # Get file information
        file_name = getattr(uploaded_file, "name", "unknown")
        file_type = getattr(uploaded_file, "type", "unknown")
        
        # Get file size
        try:
            file_content = uploaded_file.getvalue()
            file_size_bytes = len(file_content)
            file_size_mb = file_size_bytes / (1024 * 1024)
        except Exception:
            return {
                "is_valid": False, 
                "error_message": "Could not read file content",
                "file_info": {"name": file_name, "type": file_type}
            }
        
        # Check file size
        if file_size_mb > max_size_mb:
            return {
                "is_valid": False,
                "error_message": f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)",
                "file_info": {
                    "name": file_name,
                    "type": file_type, 
                    "size_mb": file_size_mb
                }
            }
        
        # Check file type
        allowed_types = {
            "text/csv", "application/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        file_extension = file_name.lower().split('.')[-1] if '.' in file_name else ""
        allowed_extensions = {"csv", "xls", "xlsx"}
        
        if file_type not in allowed_types and file_extension not in allowed_extensions:
            return {
                "is_valid": False,
                "error_message": f"Unsupported file type: {file_type}. Allowed: CSV, Excel",
                "file_info": {
                    "name": file_name,
                    "type": file_type,
                    "size_mb": file_size_mb
                }
            }
        
        # Validation passed
        return {
            "is_valid": True,
            "error_message": "",
            "file_info": {
                "name": file_name,
                "type": file_type,
                "size_mb": file_size_mb,
                "size_bytes": file_size_bytes
            }
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "error_message": f"Validation error: {str(e)}",
            "file_info": {}
        }


def extract_ballots_from_dataframe(df: Any) -> list[list[str]]:
    """Extract ballot data from a pandas DataFrame.
    
    Converts DataFrame with choice columns into list of ballot preference lists,
    handling various column naming conventions and data formats.
    
    Args:
        df: pandas DataFrame with ballot data
        
    Returns:
        List of ballots as candidate preference lists
        
    Examples:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'first_choice': ['Alice', 'Bob'], 
        ...     'second_choice': ['Bob', 'Alice']
        ... })
        >>> ballots = extract_ballots_from_dataframe(df)
        >>> len(ballots)
        2
        >>> ballots[0]
        ['Alice', 'Bob']
    """
    if df is None or df.empty:
        return []
    
    # Find choice columns (first_choice, second_choice, etc. or choice_1, choice_2, etc.)
    choice_columns = []
    
    # Look for various column naming patterns
    for col in df.columns:
        col_lower = col.lower().strip()
        if any(pattern in col_lower for pattern in [
            'choice', 'rank', 'preference', '1st', '2nd', '3rd'
        ]):
            choice_columns.append(col)
    
    if not choice_columns:
        # If no clear choice columns, use all columns
        choice_columns = list(df.columns)
    
    # Sort columns to ensure proper order (first, second, etc.)
    def sort_key(col: str) -> tuple[int, str]:
        col_lower = col.lower()
        # Extract numeric indicators
        for i, indicator in enumerate(['first', '1st', '1'], 1):
            if indicator in col_lower:
                return (i, col)
        for i, indicator in enumerate(['second', '2nd', '2'], 2):
            if indicator in col_lower:
                return (i, col)
        for i, indicator in enumerate(['third', '3rd', '3'], 3):
            if indicator in col_lower:
                return (i, col)
        # Default ordering
        return (999, col)
    
    choice_columns.sort(key=sort_key)
    
    ballots = []
    for _, row in df.iterrows():
        ballot = []
        for col in choice_columns:
            candidate = row[col]
            # Skip empty/null candidates
            if candidate and str(candidate).strip() and str(candidate).lower() not in ['nan', 'none', '']:
                candidate_name = str(candidate).strip()
                # Avoid duplicates in same ballot
                if candidate_name not in ballot:
                    ballot.append(candidate_name)
        
        # Only include non-empty ballots
        if ballot:
            ballots.append(ballot)
    
    return ballots