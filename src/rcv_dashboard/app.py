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
from .visualization.charts import (
    create_vote_progression_chart,
    create_vote_transfer_sankey,
    create_round_pie_chart,
    create_stacked_rounds_chart,
    create_elimination_timeline,
)
from .visualization.tables import (
    create_round_results_table,
    create_transfer_summary_table,
    create_candidate_summary_table,
    create_round_comparison_table,
)


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
    """Display comprehensive election results with visualizations.
    
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
    
    # Create tabs for different views
    tab_overview, tab_visualizations, tab_tables, tab_rounds = st.tabs([
        "📊 Overview", 
        "📈 Visualizations", 
        "📋 Tables", 
        "🔄 Round Details"
    ])
    
    with tab_overview:
        display_election_overview(election_result)
    
    with tab_visualizations:
        display_election_visualizations(election_result)
    
    with tab_tables:
        display_election_tables(election_result)
    
    with tab_rounds:
        display_round_by_round_results(election_result)
    
    # Option to process another election
    st.divider()
    if st.button("🔄 Process Another Election", use_container_width=True):
        st.session_state.election_result = None
        st.session_state.ballot_data = None
        st.rerun()


def display_election_overview(election_result: ElectionResult) -> None:
    """Display high-level overview of election results.
    
    Args:
        election_result: Complete election results
    """
    # Candidate summary table
    st.subheader("🥇 Final Candidate Rankings")
    candidate_summary_df = create_candidate_summary_table(election_result)
    st.dataframe(candidate_summary_df, use_container_width=True, hide_index=True)
    
    # Key insights
    st.subheader("🔍 Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Election type analysis
        if len(election_result.rounds) == 1:
            st.info("💡 **Majority Winner:** The winner achieved a majority in the first round.")
        else:
            st.info(f"💡 **Multi-Round Election:** Required {len(election_result.rounds)} rounds to determine the winner.")
        
        # Voter participation
        exhausted_final = election_result.rounds[-1].exhausted_ballots if election_result.rounds else 0
        exhausted_pct = (exhausted_final / election_result.total_ballots * 100) if election_result.total_ballots > 0 else 0
        
        if exhausted_pct > 10:
            st.warning(f"⚠️ **High ballot exhaustion:** {exhausted_pct:.1f}% of ballots were exhausted.")
        else:
            st.success(f"✅ **Low ballot exhaustion:** Only {exhausted_pct:.1f}% of ballots were exhausted.")
    
    with col2:
        # Vote transfers
        total_transfers = sum(
            len(round_result.vote_transfers) 
            for round_result in election_result.rounds 
            if round_result.vote_transfers
        )
        
        if total_transfers > 0:
            st.info(f"🔄 **Vote transfers occurred:** {total_transfers} transfer events across all rounds.")
        
        # Competitiveness
        winner_margin = election_result.winner_vote_percentage
        if winner_margin >= 60:
            st.info("📊 **Decisive victory:** Winner had strong support.")
        elif winner_margin >= 55:
            st.info("📊 **Comfortable victory:** Winner had solid support.")
        else:
            st.info("📊 **Close election:** Winner had narrow majority.")


def display_election_visualizations(election_result: ElectionResult) -> None:
    """Display interactive visualizations of election results.
    
    Args:
        election_result: Complete election results
    """
    # Chart selection
    chart_type = st.selectbox(
        "Select Visualization",
        [
            "Vote Progression (Bar Chart)",
            "Vote Transfers (Sankey Diagram)", 
            "Round Pie Charts",
            "Stacked Rounds Chart",
            "Elimination Timeline"
        ]
    )
    
    try:
        if chart_type == "Vote Progression (Bar Chart)":
            st.subheader("📊 Vote Progression Across Rounds")
            st.markdown("Track how vote counts changed for each candidate across elimination rounds.")
            fig = create_vote_progression_chart(election_result)
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Vote Transfers (Sankey Diagram)":
            st.subheader("🌊 Vote Transfer Flow")
            st.markdown("Visualize how votes flowed from eliminated candidates to remaining candidates.")
            fig = create_vote_transfer_sankey(election_result)
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Round Pie Charts":
            st.subheader("🥧 Vote Distribution by Round")
            st.markdown("See the vote share for each candidate in each round.")
            
            # Allow user to select which rounds to show
            round_options = [f"Round {i+1}" for i in range(len(election_result.rounds))]
            selected_rounds = st.multiselect(
                "Select rounds to display:", 
                round_options,
                default=round_options[:min(3, len(round_options))]  # Default to first 3 rounds
            )
            
            if selected_rounds:
                cols = st.columns(min(len(selected_rounds), 3))  # Max 3 columns
                
                for i, round_name in enumerate(selected_rounds):
                    round_idx = int(round_name.split()[1]) - 1
                    round_result = election_result.rounds[round_idx]
                    
                    with cols[i % 3]:
                        fig = create_round_pie_chart(round_result)
                        st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Stacked Rounds Chart":
            st.subheader("📚 Stacked Vote Counts")
            st.markdown("Compare vote counts across all rounds in a single stacked visualization.")
            fig = create_stacked_rounds_chart(election_result)
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Elimination Timeline":
            st.subheader("⏰ Elimination Order Timeline")
            st.markdown("Timeline showing when each candidate was eliminated.")
            fig = create_elimination_timeline(election_result)
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        if st.checkbox("Show detailed error", key=f"viz_error_{chart_type}"):
            st.code(traceback.format_exc())


def display_election_tables(election_result: ElectionResult) -> None:
    """Display comprehensive data tables for election results.
    
    Args:
        election_result: Complete election results
    """
    table_type = st.selectbox(
        "Select Table View",
        [
            "Round-by-Round Results",
            "Vote Transfer Summary", 
            "Candidate Performance",
            "Round Comparison"
        ]
    )
    
    try:
        if table_type == "Round-by-Round Results":
            st.subheader("📊 Complete Round Results")
            st.markdown("Detailed breakdown of vote counts and eliminations for every round.")
            df = create_round_results_table(election_result)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        elif table_type == "Vote Transfer Summary":
            st.subheader("🔄 Vote Transfer Details")  
            st.markdown("Summary of how votes were transferred between candidates.")
            df = create_transfer_summary_table(election_result)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        elif table_type == "Candidate Performance":
            st.subheader("🏆 Candidate Performance Analysis")
            st.markdown("Comprehensive statistics for each candidate's performance.")
            df = create_candidate_summary_table(election_result)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        elif table_type == "Round Comparison":
            st.subheader("⚖️ Round Comparison")
            st.markdown("Side-by-side comparison of selected rounds.")
            
            # Allow user to select rounds for comparison
            max_rounds = len(election_result.rounds)
            round_numbers = st.multiselect(
                "Select rounds to compare:",
                list(range(1, max_rounds + 1)),
                default=[1, max_rounds] if max_rounds > 1 else [1]
            )
            
            if len(round_numbers) >= 1:
                df = create_round_comparison_table(election_result, round_numbers)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Please select at least one round to compare.")
    
    except Exception as e:
        st.error(f"Error creating table: {str(e)}")
        if st.checkbox("Show detailed error", key=f"table_error_{table_type}"):
            st.code(traceback.format_exc())


def display_round_by_round_results(election_result: ElectionResult) -> None:
    """Display detailed round-by-round breakdown.
    
    Args:
        election_result: Complete election results
    """
    st.subheader("🔄 Round-by-Round Details")
    
    round_tabs = st.tabs([f"Round {i+1}" for i in range(len(election_result.rounds))])
    
    for i, (tab, round_result) in enumerate(zip(round_tabs, election_result.rounds)):
        with tab:
            display_round_results(round_result, i == len(election_result.rounds) - 1)


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