"""Interactive chart generation for RCV election visualization.

This module creates engaging Plotly visualizations that help users understand
ranked choice voting results through interactive charts and animations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..core.models import ElectionResult, RoundResult


def create_vote_progression_chart(election_result: ElectionResult) -> go.Figure:
    """Create an interactive bar chart showing vote progression across rounds.
    
    This visualization shows how vote counts change for each candidate across
    all elimination rounds, making it easy to see the RCV process in action.
    
    Args:
        election_result: Complete election results with all rounds
        
    Returns:
        Interactive Plotly figure with round-by-round vote progression
        
    Example:
        >>> # After running an election
        >>> fig = create_vote_progression_chart(election_result)
        >>> fig.show()  # Or st.plotly_chart(fig) in Streamlit
    """
    if not election_result.rounds:
        # Create empty chart for no data case
        fig = go.Figure()
        fig.add_annotation(
            text="No election data to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    # Extract data for all rounds and candidates
    rounds_data: list[dict[str, Any]] = []
    all_candidates = {c.name for c in election_result.candidates}
    
    for round_result in election_result.rounds:
        for candidate in all_candidates:
            vote_count = round_result.vote_counts.get(candidate, 0)
            
            # Determine candidate status for this round
            status = "Active"
            if candidate == round_result.eliminated_candidate:
                status = "Eliminated"
            elif candidate == election_result.winner and round_result == election_result.rounds[-1]:
                status = "Winner"
            
            rounds_data.append({
                "Round": f"Round {round_result.round_number}",
                "Candidate": candidate,
                "Votes": vote_count,
                "Status": status,
                "Round_Number": round_result.round_number,
                "Percentage": (vote_count / round_result.total_votes * 100) if round_result.total_votes > 0 else 0
            })
    
    # Create color mapping for candidates
    candidate_colors = _get_candidate_color_map(all_candidates)
    
    # Create the main bar chart
    fig = px.bar(
        rounds_data,
        x="Round",
        y="Votes", 
        color="Candidate",
        title="Vote Progression Across Rounds",
        color_discrete_map=candidate_colors,
        hover_data={
            "Percentage": ":.1f",
            "Status": True,
            "Round_Number": False
        },
        labels={
            "Votes": "Vote Count",
            "Round": "Election Round"
        }
    )
    
    # Add annotations for eliminations
    for i, round_result in enumerate(election_result.rounds):
        if round_result.eliminated_candidate:
            fig.add_annotation(
                x=i,
                y=max(round_result.vote_counts.values()) + (election_result.total_ballots * 0.05),
                text=f"❌ {round_result.eliminated_candidate}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(size=10, color="red"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
    
    # Add winner annotation on final round
    final_round = election_result.rounds[-1]
    winner_votes = final_round.vote_counts.get(election_result.winner, 0)
    fig.add_annotation(
        x=len(election_result.rounds) - 1,
        y=winner_votes + (election_result.total_ballots * 0.1),
        text=f"🏆 {election_result.winner}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green",
        font=dict(size=12, color="green", weight="bold"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="green",
        borderwidth=2
    )
    
    # Customize layout
    fig.update_layout(
        title={
            "text": "RCV Vote Progression Across Rounds",
            "x": 0.5,
            "font": {"size": 20, "family": "Arial, sans-serif"}
        },
        xaxis_title="Election Round",
        yaxis_title="Vote Count",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right", 
            x=1
        ),
        height=500,
        showlegend=True,
        plot_bgcolor="rgba(248,249,250,0.8)"
    )
    
    # Add majority threshold line if applicable
    majority_threshold = election_result.majority_threshold
    if majority_threshold > 0:
        fig.add_hline(
            y=majority_threshold,
            line_dash="dash",
            line_color="purple",
            annotation_text=f"Majority Threshold ({majority_threshold})",
            annotation_position="top right"
        )
    
    return fig


def create_vote_transfer_sankey(election_result: ElectionResult) -> go.Figure:
    """Create a Sankey diagram showing vote transfers between candidates.
    
    This visualization shows how votes flow from eliminated candidates to
    remaining candidates, illustrating the vote transfer process in RCV.
    
    Args:
        election_result: Complete election results with transfer information
        
    Returns:
        Interactive Plotly Sankey diagram
        
    Example:
        >>> fig = create_vote_transfer_sankey(election_result)
        >>> fig.show()
    """
    if len(election_result.rounds) <= 1:
        # No transfers to show
        fig = go.Figure()
        fig.add_annotation(
            text="No vote transfers to display<br>(Election decided in first round)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Vote Transfer Flow")
        return fig
    
    # Collect all transfer data
    nodes = []
    links = []
    node_colors = []
    
    # Create nodes for each candidate in each round
    node_map: dict[str, int] = {}
    node_index = 0
    
    # Add initial round nodes (sources)
    for candidate in election_result.candidates:
        first_round = election_result.rounds[0]
        if candidate.name in first_round.vote_counts and first_round.vote_counts[candidate.name] > 0:
            node_key = f"{candidate.name}_R1"
            nodes.append(f"{candidate.name}<br>Round 1")
            node_map[node_key] = node_index
            node_colors.append(_get_candidate_color_hex(candidate.name, len(election_result.candidates)))
            node_index += 1
    
    # Add subsequent round nodes and links
    for round_num, round_result in enumerate(election_result.rounds[1:], 2):
        # Add nodes for active candidates in this round
        for candidate_name, vote_count in round_result.vote_counts.items():
            if vote_count > 0:
                node_key = f"{candidate_name}_R{round_num}"
                nodes.append(f"{candidate_name}<br>Round {round_num}")
                node_map[node_key] = node_index
                node_colors.append(_get_candidate_color_hex(candidate_name, len(election_result.candidates)))
                node_index += 1
    
    # Create links for vote transfers
    for round_num, round_result in enumerate(election_result.rounds[1:], 2):
        prev_round = election_result.rounds[round_num - 2]
        
        # Handle transfers from eliminated candidate
        if round_result.vote_transfers:
            eliminated = prev_round.eliminated_candidate
            if eliminated:
                eliminated_key = f"{eliminated}_R{round_num-1}"
                
                # Create links for each transfer
                for transfer in round_result.vote_transfers:
                    target_key = f"{transfer.to_candidate}_R{round_num}"
                    
                    if eliminated_key in node_map and target_key in node_map:
                        links.append({
                            "source": node_map[eliminated_key],
                            "target": node_map[target_key], 
                            "value": transfer.vote_count,
                            "label": f"{transfer.vote_count} votes"
                        })
        
        # Handle continuing votes (candidates who weren't eliminated)
        for candidate_name, current_votes in round_result.vote_counts.items():
            prev_votes = prev_round.vote_counts.get(candidate_name, 0)
            
            # Calculate votes that continued (not from transfers)
            transfer_received = sum(
                t.vote_count for t in round_result.vote_transfers 
                if t.to_candidate == candidate_name
            )
            continuing_votes = prev_votes
            
            if continuing_votes > 0 and candidate_name != prev_round.eliminated_candidate:
                prev_key = f"{candidate_name}_R{round_num-1}"
                current_key = f"{candidate_name}_R{round_num}"
                
                if prev_key in node_map and current_key in node_map:
                    links.append({
                        "source": node_map[prev_key],
                        "target": node_map[current_key],
                        "value": continuing_votes,
                        "label": f"{continuing_votes} continuing"
                    })
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=node_colors
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            label=[link["label"] for link in links]
        )
    )])
    
    fig.update_layout(
        title={
            "text": "Vote Transfer Flow in RCV Election",
            "x": 0.5,
            "font": {"size": 20}
        },
        font_size=12,
        height=600
    )
    
    return fig


def create_round_pie_chart(round_result: RoundResult, title_suffix: str = "") -> go.Figure:
    """Create a pie chart for a specific election round.
    
    Shows the vote distribution for a single round, highlighting
    the candidate who was eliminated (if any).
    
    Args:
        round_result: Results for a specific round
        title_suffix: Optional suffix for the chart title
        
    Returns:
        Interactive Plotly pie chart
        
    Example:
        >>> round1 = election_result.rounds[0]
        >>> fig = create_round_pie_chart(round1, "- First Round")
        >>> fig.show()
    """
    if not round_result.vote_counts:
        fig = go.Figure()
        fig.add_annotation(
            text="No vote data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Prepare data
    candidates = list(round_result.vote_counts.keys())
    votes = list(round_result.vote_counts.values())
    
    # Create color map and highlight eliminated candidate
    colors = []
    text_info = []
    
    for candidate in candidates:
        if candidate == round_result.eliminated_candidate:
            colors.append("#ff6b6b")  # Red for eliminated
            text_info.append(f"{candidate}<br>❌ Eliminated")
        else:
            colors.append(_get_candidate_color_hex(candidate, len(candidates)))
            text_info.append(candidate)
    
    # Calculate percentages
    total_votes = sum(votes)
    percentages = [v/total_votes * 100 if total_votes > 0 else 0 for v in votes]
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=candidates,
        values=votes,
        text=text_info,
        textinfo="label+percent+value",
        textposition="auto",
        marker=dict(colors=colors, line=dict(color="#000000", width=2)),
        hovertemplate="<b>%{label}</b><br>" +
                      "Votes: %{value}<br>" +
                      "Percentage: %{percent}<br>" +
                      "<extra></extra>",
        pull=[0.1 if c == round_result.eliminated_candidate else 0 for c in candidates]
    )])
    
    fig.update_layout(
        title={
            "text": f"Round {round_result.round_number} Results{title_suffix}",
            "x": 0.5,
            "font": {"size": 18}
        },
        annotations=[
            dict(
                text=f"Total Votes: {total_votes}<br>Exhausted: {round_result.exhausted_ballots}",
                x=0.5, y=0.1,
                font_size=12,
                showarrow=False
            )
        ],
        height=400,
        showlegend=True
    )
    
    return fig


def create_stacked_rounds_chart(election_result: ElectionResult) -> go.Figure:
    """Create a stacked bar chart showing all rounds side by side.
    
    This gives an overview of how the election evolved across all rounds
    in a compact format.
    
    Args:
        election_result: Complete election results
        
    Returns:
        Interactive Plotly stacked bar chart
        
    Example:
        >>> fig = create_stacked_rounds_chart(election_result)
        >>> fig.show()
    """
    if not election_result.rounds:
        fig = go.Figure()
        fig.add_annotation(text="No election data", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Prepare data for stacked chart
    candidates = [c.name for c in election_result.candidates]
    candidate_colors = _get_candidate_color_map(candidates)
    
    fig = go.Figure()
    
    # Add trace for each candidate
    for candidate in candidates:
        votes_by_round = []
        round_labels = []
        
        for round_result in election_result.rounds:
            votes_by_round.append(round_result.vote_counts.get(candidate, 0))
            round_labels.append(f"Round {round_result.round_number}")
        
        fig.add_trace(go.Bar(
            name=candidate,
            x=round_labels,
            y=votes_by_round,
            marker_color=candidate_colors[candidate],
            hovertemplate=f"<b>{candidate}</b><br>" +
                          "Round: %{x}<br>" +
                          "Votes: %{y}<br>" +
                          "<extra></extra>"
        ))
    
    # Add majority threshold line
    fig.add_hline(
        y=election_result.majority_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Majority ({election_result.majority_threshold})"
    )
    
    fig.update_layout(
        title={
            "text": "Vote Distribution Across All Rounds",
            "x": 0.5,
            "font": {"size": 20}
        },
        xaxis_title="Election Round",
        yaxis_title="Vote Count",
        barmode="stack",
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )
    
    return fig


def create_elimination_timeline(election_result: ElectionResult) -> go.Figure:
    """Create a timeline showing the order of candidate elimination.
    
    This visualization helps users understand the sequence of eliminations
    and when each candidate was removed from the contest.
    
    Args:
        election_result: Complete election results
        
    Returns:
        Interactive Plotly timeline chart
        
    Example:
        >>> fig = create_elimination_timeline(election_result)
        >>> fig.show()
    """
    # Collect elimination data
    eliminations = []
    
    for round_result in election_result.rounds:
        if round_result.eliminated_candidate:
            eliminations.append({
                "candidate": round_result.eliminated_candidate,
                "round": round_result.round_number,
                "votes": round_result.vote_counts.get(round_result.eliminated_candidate, 0),
                "total_votes": round_result.total_votes
            })
    
    if not eliminations:
        fig = go.Figure()
        fig.add_annotation(
            text="No eliminations occurred<br>(Winner determined in first round)",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Elimination Timeline")
        return fig
    
    # Create timeline
    fig = go.Figure()
    
    # Add elimination points
    rounds = [e["round"] for e in eliminations]
    candidates = [e["candidate"] for e in eliminations]
    votes = [e["votes"] for e in eliminations]
    
    fig.add_trace(go.Scatter(
        x=rounds,
        y=list(range(len(eliminations))),
        mode="markers+text+lines",
        marker=dict(
            size=15,
            color="red",
            symbol="x",
            line=dict(width=2, color="darkred")
        ),
        text=candidates,
        textposition="middle right",
        textfont=dict(size=12, color="darkred"),
        name="Eliminations",
        hovertemplate="<b>%{text}</b><br>" +
                      "Eliminated in Round: %{x}<br>" +
                      "Final Votes: " + str(votes[0] if votes else 0) + "<br>" +
                      "<extra></extra>",
        line=dict(color="red", width=2, dash="dot")
    ))
    
    # Add winner point
    fig.add_trace(go.Scatter(
        x=[len(election_result.rounds)],
        y=[len(eliminations)],
        mode="markers+text",
        marker=dict(
            size=20,
            color="gold",
            symbol="star",
            line=dict(width=2, color="orange")
        ),
        text=[f"🏆 {election_result.winner}"],
        textposition="middle right",
        textfont=dict(size=14, color="green", weight="bold"),
        name="Winner",
        hovertemplate=f"<b>{election_result.winner}</b><br>" +
                      f"Won in Round: {len(election_result.rounds)}<br>" +
                      f"Final Vote %: {election_result.winner_vote_percentage:.1f}%<br>" +
                      "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            "text": "Candidate Elimination Timeline",
            "x": 0.5,
            "font": {"size": 20}
        },
        xaxis=dict(
            title="Election Round",
            tickmode="linear",
            tick0=1,
            dtick=1,
            range=[0.5, len(election_result.rounds) + 0.5]
        ),
        yaxis=dict(
            title="Elimination Order",
            tickmode="linear",
            tick0=0,
            dtick=1,
            range=[-0.5, len(eliminations) + 0.5],
            ticktext=["First Out"] + [f"{i+1}" for i in range(len(eliminations)-1)] + ["Winner"],
            tickvals=list(range(len(eliminations) + 1))
        ),
        height=400,
        showlegend=False,
        hovermode="closest"
    )
    
    return fig


def _get_candidate_color_map(candidates: Sequence[str]) -> dict[str, str]:
    """Generate a consistent color mapping for candidates.
    
    Args:
        candidates: List of candidate names
        
    Returns:
        Dictionary mapping candidate names to hex colors
    """
    # Use a pleasant color palette
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
        "#c49c94", "#f7b6d3", "#c7c7c7", "#dbdb8d", "#9edae5"
    ]
    
    return {
        candidate: colors[i % len(colors)]
        for i, candidate in enumerate(sorted(candidates))
    }


def _get_candidate_color_hex(candidate: str, total_candidates: int) -> str:
    """Get a hex color for a specific candidate.
    
    Args:
        candidate: Candidate name
        total_candidates: Total number of candidates (for color distribution)
        
    Returns:
        Hex color string
    """
    color_map = _get_candidate_color_map([candidate])
    return color_map.get(candidate, "#1f77b4")