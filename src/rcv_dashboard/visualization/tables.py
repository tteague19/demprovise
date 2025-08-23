"""Formatted table generation for RCV election results.

This module creates well-formatted pandas DataFrames for displaying
election results in tables with proper sorting, styling, and formatting.
"""

from __future__ import annotations

import pandas as pd

from ..core.models import ElectionResult, RoundResult


def create_round_results_table(election_result: ElectionResult) -> pd.DataFrame:
    """Create a comprehensive table showing results for all rounds.
    
    This table provides a complete overview of how vote counts changed
    across all elimination rounds in a compact, sortable format.
    
    Args:
        election_result: Complete election results with all rounds
        
    Returns:
        Formatted DataFrame with round-by-round results
        
    Example:
        >>> df = create_round_results_table(election_result)
        >>> st.dataframe(df)  # In Streamlit
    """
    if not election_result.rounds:
        return pd.DataFrame({"Message": ["No election data available"]})
    
    # Collect data for all candidates across all rounds
    table_data: list[dict[str, any]] = []
    all_candidates = {c.name for c in election_result.candidates}
    
    # Add a row for each round
    for round_result in election_result.rounds:
        row_data = {
            "Round": round_result.round_number,
            "Total Votes": round_result.total_votes,
            "Exhausted Ballots": round_result.exhausted_ballots,
        }
        
        # Add vote counts for each candidate
        for candidate in sorted(all_candidates):
            votes = round_result.vote_counts.get(candidate, 0)
            percentage = (votes / round_result.total_votes * 100) if round_result.total_votes > 0 else 0
            
            # Format as "votes (percentage%)"
            if votes > 0:
                row_data[candidate] = f"{votes} ({percentage:.1f}%)"
            else:
                row_data[candidate] = "0 (0.0%)"
        
        # Add elimination info
        if round_result.eliminated_candidate:
            row_data["Eliminated"] = f"❌ {round_result.eliminated_candidate}"
        else:
            # Check if this is the final round with a winner
            if round_result == election_result.rounds[-1]:
                row_data["Eliminated"] = f"🏆 {election_result.winner} WINS"
            else:
                row_data["Eliminated"] = "—"
        
        table_data.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Reorder columns for better display
    base_columns = ["Round", "Total Votes", "Exhausted Ballots"]
    candidate_columns = sorted(all_candidates)
    final_columns = base_columns + candidate_columns + ["Eliminated"]
    
    # Ensure all columns exist and reorder
    for col in final_columns:
        if col not in df.columns:
            df[col] = "—"
    
    df = df[final_columns]
    
    return df


def create_transfer_summary_table(election_result: ElectionResult) -> pd.DataFrame:
    """Create a table summarizing all vote transfers in the election.
    
    Shows how votes moved from eliminated candidates to remaining
    candidates throughout the election process.
    
    Args:
        election_result: Complete election results with transfer data
        
    Returns:
        Formatted DataFrame with vote transfer details
        
    Example:
        >>> df = create_transfer_summary_table(election_result)
        >>> st.dataframe(df)
    """
    transfer_data: list[dict[str, any]] = []
    
    for round_result in election_result.rounds:
        if round_result.vote_transfers:
            eliminated = round_result.eliminated_candidate
            total_transferred = sum(t.vote_count for t in round_result.vote_transfers)
            
            # Add summary row for this elimination
            transfer_data.append({
                "Round": round_result.round_number,
                "Eliminated Candidate": f"❌ {eliminated}",
                "From": eliminated,
                "To": "Various",
                "Votes Transferred": total_transferred,
                "Transfer Type": "Summary",
                "Percentage": "100.0%"
            })
            
            # Add detailed transfer rows
            for transfer in round_result.vote_transfers:
                percentage = (transfer.vote_count / total_transferred * 100) if total_transferred > 0 else 0
                transfer_data.append({
                    "Round": round_result.round_number,
                    "Eliminated Candidate": "",
                    "From": transfer.from_candidate,
                    "To": f"→ {transfer.to_candidate}",
                    "Votes Transferred": transfer.vote_count,
                    "Transfer Type": "Detail",
                    "Percentage": f"{percentage:.1f}%"
                })
        
        # Check for exhausted ballots
        if round_result.exhausted_ballots > 0:
            prev_round_exhausted = 0
            if len(election_result.rounds) > 1:
                prev_round_idx = round_result.round_number - 2
                if prev_round_idx >= 0:
                    prev_round_exhausted = election_result.rounds[prev_round_idx].exhausted_ballots
            
            newly_exhausted = round_result.exhausted_ballots - prev_round_exhausted
            if newly_exhausted > 0:
                transfer_data.append({
                    "Round": round_result.round_number,
                    "Eliminated Candidate": "",
                    "From": round_result.eliminated_candidate or "Various",
                    "To": "💔 Exhausted",
                    "Votes Transferred": newly_exhausted,
                    "Transfer Type": "Exhausted",
                    "Percentage": "—"
                })
    
    if not transfer_data:
        return pd.DataFrame({
            "Message": ["No vote transfers occurred (winner decided in first round)"]
        })
    
    df = pd.DataFrame(transfer_data)
    
    # Clean up display
    display_columns = ["Round", "From", "To", "Votes Transferred", "Percentage"]
    df_display = df[display_columns].copy()
    
    return df_display


def create_candidate_summary_table(election_result: ElectionResult) -> pd.DataFrame:
    """Create a summary table with final candidate statistics.
    
    Shows key metrics for each candidate including their performance
    across rounds and final outcome.
    
    Args:
        election_result: Complete election results
        
    Returns:
        Formatted DataFrame with candidate performance summary
        
    Example:
        >>> df = create_candidate_summary_table(election_result)
        >>> st.dataframe(df)
    """
    candidate_data: list[dict[str, any]] = []
    
    for candidate_info in election_result.candidates:
        # Calculate candidate statistics
        first_choice_votes = 0
        peak_votes = 0
        rounds_active = 0
        
        # Analyze performance across rounds
        for round_result in election_result.rounds:
            votes_this_round = round_result.vote_counts.get(candidate_info.name, 0)
            
            # First round = first choice votes
            if round_result.round_number == 1:
                first_choice_votes = votes_this_round
            
            # Track peak performance
            if votes_this_round > peak_votes:
                peak_votes = votes_this_round
            
            # Count rounds active (had votes)
            if votes_this_round > 0:
                rounds_active += 1
        
        # Determine status emoji and description
        if candidate_info.status == "winner":
            status_display = "🏆 Winner"
            status_color = "success"
        elif candidate_info.status == "eliminated":
            status_display = f"❌ Eliminated (Round {candidate_info.elimination_round})"
            status_color = "error"
        else:
            status_display = "🔄 Active"
            status_color = "info"
        
        # Calculate percentages
        first_choice_pct = (first_choice_votes / election_result.total_ballots * 100) if election_result.total_ballots > 0 else 0
        final_pct = (candidate_info.vote_count / election_result.total_ballots * 100) if election_result.total_ballots > 0 else 0
        peak_pct = (peak_votes / election_result.total_ballots * 100) if election_result.total_ballots > 0 else 0
        
        candidate_data.append({
            "Candidate": candidate_info.name,
            "Status": status_display,
            "First Choice Votes": f"{first_choice_votes} ({first_choice_pct:.1f}%)",
            "Peak Votes": f"{peak_votes} ({peak_pct:.1f}%)",
            "Final Votes": f"{candidate_info.vote_count} ({final_pct:.1f}%)",
            "Rounds Active": f"{rounds_active}/{len(election_result.rounds)}",
            "Elimination Round": candidate_info.elimination_round or "—",
        })
    
    df = pd.DataFrame(candidate_data)
    
    # Sort by final votes (descending) to show ranking
    if "Final Votes" in df.columns:
        # Extract numeric values for sorting
        df["_sort_key"] = df["Final Votes"].str.extract(r"(\d+)").astype(int)
        df = df.sort_values("_sort_key", ascending=False)
        df = df.drop("_sort_key", axis=1)
    
    return df


def create_round_comparison_table(election_result: ElectionResult, round_numbers: list[int]) -> pd.DataFrame:
    """Create a side-by-side comparison of specific rounds.
    
    Useful for comparing key moments in the election, such as
    before and after major eliminations.
    
    Args:
        election_result: Complete election results
        round_numbers: List of round numbers to compare
        
    Returns:
        DataFrame comparing vote counts across specified rounds
        
    Example:
        >>> df = create_round_comparison_table(election_result, [1, 3])
        >>> st.dataframe(df)
    """
    if not round_numbers or not election_result.rounds:
        return pd.DataFrame({"Message": ["No data available for comparison"]})
    
    # Filter to valid round numbers
    valid_rounds = [r for r in round_numbers if 1 <= r <= len(election_result.rounds)]
    if not valid_rounds:
        return pd.DataFrame({"Message": ["Invalid round numbers specified"]})
    
    # Get all candidates
    all_candidates = sorted({c.name for c in election_result.candidates})
    
    # Build comparison data
    comparison_data = []
    
    for candidate in all_candidates:
        row = {"Candidate": candidate}
        
        for round_num in valid_rounds:
            round_result = election_result.rounds[round_num - 1]  # Convert to 0-indexed
            votes = round_result.vote_counts.get(candidate, 0)
            percentage = (votes / round_result.total_votes * 100) if round_result.total_votes > 0 else 0
            
            # Check if eliminated in this round
            if candidate == round_result.eliminated_candidate:
                row[f"Round {round_num}"] = f"{votes} ({percentage:.1f}%) ❌"
            elif votes == 0:
                row[f"Round {round_num}"] = "0 (0.0%)"
            else:
                row[f"Round {round_num}"] = f"{votes} ({percentage:.1f}%)"
        
        # Calculate change between first and last round in comparison
        if len(valid_rounds) >= 2:
            first_round = election_result.rounds[valid_rounds[0] - 1]
            last_round = election_result.rounds[valid_rounds[-1] - 1]
            
            first_votes = first_round.vote_counts.get(candidate, 0)
            last_votes = last_round.vote_counts.get(candidate, 0)
            change = last_votes - first_votes
            
            if change > 0:
                row["Change"] = f"+{change}"
            elif change < 0:
                row["Change"] = str(change)
            else:
                row["Change"] = "0"
        
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    return df


def style_results_table(df: pd.DataFrame, table_type: str = "results") -> pd.DataFrame:
    """Apply consistent styling to results tables for better readability.
    
    This function can be used to add consistent styling across different
    table types in the application.
    
    Args:
        df: DataFrame to style
        table_type: Type of table for specific styling rules
        
    Returns:
        Styled DataFrame (note: styling may not be preserved in all contexts)
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    styled_df = df.copy()
    
    # Apply table-specific styling logic
    if table_type == "results":
        # Highlight winner rows
        if "Status" in styled_df.columns:
            styled_df.loc[styled_df["Status"].str.contains("🏆", na=False), "Status"] = \
                styled_df.loc[styled_df["Status"].str.contains("🏆", na=False), "Status"]
    
    elif table_type == "transfers":
        # Bold summary rows
        if "Transfer Type" in styled_df.columns:
            # This is a placeholder for styling that would be applied in Streamlit
            pass
    
    return styled_df