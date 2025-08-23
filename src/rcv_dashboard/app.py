"""Main Streamlit application for the RCV Dashboard.

This is the entry point for the RCV Dashboard web application, providing
an intuitive interface for uploading ballots, processing elections, and
viewing results.
"""

from __future__ import annotations

import traceback
from typing import Any

import streamlit as st
from pydantic import ValidationError

from .core.ballot_loader import load_ballots_from_uploaded_file
from .core.models import AppSettings, ElectionResult
from .core.rcv_processor import RCVProcessor


def main() -> None:
    """Main entry point for the Streamlit application."""
    # Configure the page
    st.set_page_config(
        page_title="RCV Dashboard",
        page_icon="🗳️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load application settings
    settings = AppSettings()
    
    # Initialize session state
    if "election_result" not in st.session_state:
        st.session_state.election_result = None
    if "ballot_data" not in st.session_state:
        st.session_state.ballot_data = None
    
    # Main application layout
    st.title("🗳️ Ranked Choice Voting Dashboard")
    st.markdown("""
    Upload your ballot data to analyze ranked choice voting elections with comprehensive
    visualizations and detailed results.
    """)
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("Upload Ballot Data")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a ballot file",
            type=["csv", "xlsx", "xls"],
            help="Upload a CSV or Excel file containing ballot preferences"
        )
        
        if uploaded_file:
            process_uploaded_file(uploaded_file, settings)
        
        # Settings section
        st.header("Settings")
        
        # Display current settings (read-only for now)
        with st.expander("Application Settings"):
            st.json({
                "Max file size (MB)": settings.max_file_size_mb,
                "Max candidates": settings.max_candidates,
                "Max ballots": settings.max_ballots,
                "Chart theme": settings.chart_theme,
            })
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display main content based on application state
        if st.session_state.election_result:
            display_election_results(st.session_state.election_result)
        elif st.session_state.ballot_data:
            display_ballot_preview(st.session_state.ballot_data)
        else:
            display_welcome_screen()
    
    with col2:
        # Right sidebar with additional information
        display_information_panel()


def process_uploaded_file(uploaded_file: Any, settings: AppSettings) -> None:
    """Process an uploaded ballot file and update session state.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        settings: Application settings for validation
    """
    try:
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            st.error(f"File too large ({file_size_mb:.1f}MB). Maximum size: {settings.max_file_size_mb}MB")
            return
        
        # Load and validate ballot data
        with st.spinner("Loading ballot data..."):
            ballot_data = load_ballots_from_uploaded_file(uploaded_file)
        
        # Validate against settings
        if len(ballot_data.candidates) > settings.max_candidates:
            st.error(f"Too many candidates ({len(ballot_data.candidates)}). Maximum: {settings.max_candidates}")
            return
        
        if ballot_data.total_ballots > settings.max_ballots:
            st.error(f"Too many ballots ({ballot_data.total_ballots}). Maximum: {settings.max_ballots}")
            return
        
        # Store in session state
        st.session_state.ballot_data = ballot_data
        st.session_state.election_result = None
        
        st.success(f"✅ Loaded {ballot_data.total_ballots} ballots with {len(ballot_data.candidates)} candidates")
        
        if ballot_data.invalid_ballots > 0:
            st.warning(f"⚠️ {ballot_data.invalid_ballots} invalid ballots were excluded")
    
    except ValidationError as e:
        st.error("Validation Error:")
        for error in e.errors():
            st.error(f"- {error['loc'][0] if error['loc'] else 'Unknown'}: {error['msg']}")
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        if st.checkbox("Show detailed error"):
            st.code(traceback.format_exc())


def display_ballot_preview(ballot_data: Any) -> None:
    """Display a preview of loaded ballot data and run election button.
    
    Args:
        ballot_data: Loaded and validated ballot data
    """
    st.header("📊 Ballot Data Preview")
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ballots", ballot_data.total_ballots)
    
    with col2:
        st.metric("Candidates", len(ballot_data.candidates))
    
    with col3:
        st.metric("Invalid Ballots", ballot_data.invalid_ballots)
    
    # Show candidates
    st.subheader("Candidates")
    candidates_per_row = 3
    candidate_list = sorted(ballot_data.candidates)
    
    for i in range(0, len(candidate_list), candidates_per_row):
        cols = st.columns(candidates_per_row)
        for j, candidate in enumerate(candidate_list[i:i+candidates_per_row]):
            with cols[j]:
                st.write(f"• {candidate}")
    
    # Show sample ballots
    st.subheader("Sample Ballots")
    num_samples = min(5, len(ballot_data.ballots))
    
    sample_data = []
    for i in range(num_samples):
        ballot = ballot_data.ballots[i]
        row = {"Ballot": i + 1}
        
        for rank, candidate in enumerate(ballot[:5]):  # Show up to 5 preferences
            row[f"Choice {rank + 1}"] = candidate
        
        sample_data.append(row)
    
    if sample_data:
        st.dataframe(sample_data, use_container_width=True)
    
    # Run election button
    st.subheader("Run Election")
    
    if st.button("🏆 Process RCV Election", type="primary", use_container_width=True):
        run_rcv_election(ballot_data)


def run_rcv_election(ballot_data: Any) -> None:
    """Run the RCV election and update session state with results.
    
    Args:
        ballot_data: Validated ballot data
    """
    try:
        with st.spinner("Processing RCV election..."):
            processor = RCVProcessor(ballot_data)
            election_result = processor.run_election()
        
        # Store results in session state
        st.session_state.election_result = election_result
        
        # Show success message
        st.success(f"🎉 Election complete! Winner: **{election_result.winner}**")
        st.balloons()
    
    except Exception as e:
        st.error(f"Error processing election: {str(e)}")
        if st.checkbox("Show detailed error", key="election_error"):
            st.code(traceback.format_exc())


def display_election_results(election_result: ElectionResult) -> None:
    """Display comprehensive election results.
    
    Args:
        election_result: Complete election results from RCV processing
    """
    st.header("🏆 Election Results")
    
    # Winner announcement
    st.success(f"### Winner: {election_result.winner}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Winner Vote %", f"{election_result.winner_vote_percentage:.1f}%")
    
    with col2:
        st.metric("Total Ballots", election_result.total_ballots)
    
    with col3:
        st.metric("Rounds", len(election_result.rounds))
    
    with col4:
        st.metric("Majority Threshold", election_result.majority_threshold)
    
    # Round-by-round results
    st.subheader("📊 Round-by-Round Results")
    
    tabs = st.tabs([f"Round {i+1}" for i in range(len(election_result.rounds))])
    
    for i, (tab, round_result) in enumerate(zip(tabs, election_result.rounds)):
        with tab:
            display_round_results(round_result, i == len(election_result.rounds) - 1)
    
    # Final candidate standings
    st.subheader("🥇 Final Candidate Rankings")
    
    candidate_data = []
    for candidate in election_result.candidates:
        candidate_data.append({
            "Candidate": candidate.name,
            "Status": candidate.status.title(),
            "Final Votes": candidate.vote_count,
            "Eliminated in Round": candidate.elimination_round or "N/A"
        })
    
    # Sort by final votes (descending)
    candidate_data.sort(key=lambda x: x["Final Votes"], reverse=True)
    st.dataframe(candidate_data, use_container_width=True, hide_index=True)
    
    # Option to process another election
    if st.button("🔄 Process Another Election", use_container_width=True):
        st.session_state.election_result = None
        st.session_state.ballot_data = None
        st.rerun()


def display_round_results(round_result: Any, is_final: bool = False) -> None:
    """Display results for a specific round.
    
    Args:
        round_result: Results for this specific round
        is_final: Whether this is the final round
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Vote counts for this round
        vote_data = [
            {"Candidate": candidate, "Votes": votes}
            for candidate, votes in sorted(
                round_result.vote_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
        ]
        
        st.dataframe(vote_data, use_container_width=True, hide_index=True)
    
    with col2:
        # Round information
        st.metric("Total Votes", round_result.total_votes)
        st.metric("Exhausted Ballots", round_result.exhausted_ballots)
        
        if round_result.eliminated_candidate and not is_final:
            st.error(f"Eliminated: {round_result.eliminated_candidate}")
        elif is_final:
            winner = max(round_result.vote_counts, key=round_result.vote_counts.get)
            st.success(f"Winner: {winner}")
    
    # Vote transfers (if any)
    if round_result.vote_transfers:
        st.write("**Vote Transfers:**")
        for transfer in round_result.vote_transfers:
            st.write(f"• {transfer.vote_count} votes → {transfer.to_candidate}")


def display_welcome_screen() -> None:
    """Display the welcome screen when no data is loaded."""
    st.header("Welcome to the RCV Dashboard! 🗳️")
    
    st.markdown("""
    ### What is Ranked Choice Voting?
    
    Ranked Choice Voting (RCV) allows voters to rank candidates by preference. If no candidate
    receives a majority of first-choice votes, the candidate with the fewest votes is eliminated
    and their votes are transferred to voters' next choices. This process continues until someone
    has a majority.
    
    ### How to Use This Dashboard:
    
    1. **Upload your ballot data** using the sidebar (CSV or Excel format)
    2. **Preview your data** to ensure it loaded correctly
    3. **Run the election** to see round-by-round results
    4. **Analyze the results** with detailed breakdowns
    
    ### Expected File Format:
    
    Your file should have columns for voter preferences:
    - `Choice 1`, `Choice 2`, `Choice 3`, etc., or
    - `1st Choice`, `2nd Choice`, `3rd Choice`, etc., or
    - `Rank 1`, `Rank 2`, `Rank 3`, etc.
    
    Each row represents one ballot with the voter's ranked preferences.
    """)
    
    # Sample data format
    st.subheader("📋 Example File Format")
    
    sample_data = [
        {"Choice 1": "Alice Johnson", "Choice 2": "Bob Smith", "Choice 3": "Charlie Brown"},
        {"Choice 1": "Bob Smith", "Choice 2": "Alice Johnson", "Choice 3": ""},
        {"Choice 1": "Charlie Brown", "Choice 2": "Alice Johnson", "Choice 3": "Bob Smith"},
        {"Choice 1": "Alice Johnson", "Choice 2": "", "Choice 3": ""},
    ]
    
    st.dataframe(sample_data, use_container_width=True, hide_index=True)


def display_information_panel() -> None:
    """Display additional information and help in the right panel."""
    st.header("ℹ️ Information")
    
    with st.expander("About RCV"):
        st.markdown("""
        **Ranked Choice Voting** ensures that winners have broad support by allowing
        voters to express their full preferences rather than choosing just one candidate.
        
        **Benefits:**
        - Eliminates the "spoiler effect"
        - Encourages positive campaigning
        - Ensures majority support for winners
        - Gives voters more voice in elections
        """)
    
    with st.expander("File Requirements"):
        st.markdown("""
        **Supported formats:** CSV, XLSX, XLS
        
        **Column names:** Flexible - we support:
        - Choice 1, Choice 2, Choice 3...
        - 1st Choice, 2nd Choice, 3rd Choice...
        - Rank 1, Rank 2, Rank 3...
        - First, Second, Third...
        
        **Data requirements:**
        - At least 2 candidates
        - At least 1 valid ballot
        - No duplicate rankings in a single ballot
        """)
    
    with st.expander("Need Help?"):
        st.markdown("""
        **Common issues:**
        - Ensure column headers are in the expected format
        - Check for duplicate candidate names (typos)
        - Verify no voter ranked the same candidate twice
        - Make sure file size is under the limit
        
        **Tips:**
        - Clean your data before uploading
        - Use consistent candidate name spelling
        - Remove empty rows and columns
        """)


if __name__ == "__main__":
    main()