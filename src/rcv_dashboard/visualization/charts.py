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
    
    # Track when each candidate was eliminated
    elimination_rounds = {}
    for candidate_info in election_result.candidates:
        if candidate_info.elimination_round:
            elimination_rounds[candidate_info.name] = candidate_info.elimination_round
    
    for round_result in election_result.rounds:
        for candidate in all_candidates:
            vote_count = round_result.vote_counts.get(candidate, 0)
            
            # Determine candidate status for this round
            status = "Active"
            
            # Check if candidate was eliminated in a previous round
            if candidate in elimination_rounds:
                if elimination_rounds[candidate] <= round_result.round_number:
                    if elimination_rounds[candidate] == round_result.round_number:
                        status = "Eliminated"
                    else:
                        # Candidate was eliminated in previous round - don't show in this round
                        continue
            
            # Check if this is the winner in the final round
            if candidate == election_result.winner and round_result == election_result.rounds[-1]:
                status = "Winner"
            
            # Only add candidates who are still active or being eliminated this round
            if vote_count > 0 or status == "Eliminated":
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
        title="RCV Vote Progression (Eliminated Candidates Hidden After Elimination)",
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
    """Create a Sankey diagram showing RCV vote redistribution flows.
    
    This visualization shows how votes redistribute when candidates are eliminated.
    Each round shows candidates with their vote totals, and flows show how
    eliminated candidate votes transfer to remaining candidates based on ballot preferences.
    
    Args:
        election_result: Complete election results with transfer information
        
    Returns:
        Interactive Plotly Sankey diagram showing vote redistribution flow
        
    Example:
        >>> fig = create_vote_transfer_sankey(election_result)
        >>> fig.show()
    """
    if len(election_result.rounds) <= 1:
        # Single round election - show simple result
        fig = go.Figure()
        final_round = election_result.rounds[0]
        
        fig.add_annotation(
            text=f"🏆 {election_result.winner} won with majority in Round 1!<br><br>" +
                 f"Final votes: {final_round.vote_counts.get(election_result.winner, 0):,}<br>" +
                 f"No vote transfers needed",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="darkgreen"),
            bgcolor="rgba(144, 238, 144, 0.2)",
            bordercolor="green",
            borderwidth=2,
            borderpad=20
        )
        fig.update_layout(
            title="RCV Vote Flow - First Round Victory",
            height=400,
            showlegend=False
        )
        return fig
    
    # Build vote redistribution flow
    nodes = []
    node_colors = []
    links = []
    node_map = {}
    node_index = 0
    
    # Get consistent colors for candidates
    all_candidates = [c.name for c in election_result.candidates]
    candidate_colors = {}
    base_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, candidate in enumerate(all_candidates):
        candidate_colors[candidate] = base_colors[i % len(base_colors)]
    
    # Create nodes for each round showing candidate vote totals
    for round_idx, round_result in enumerate(election_result.rounds):
        round_num = round_result.round_number
        
        # Add nodes for all candidates with votes in this round
        for candidate_name, vote_count in round_result.vote_counts.items():
            if vote_count > 0:
                node_key = f"{candidate_name}_R{round_num}"
                
                # Special labeling for eliminated candidates
                if candidate_name == round_result.eliminated_candidate:
                    node_label = f"{candidate_name}\nRound {round_num}\n({vote_count:,} votes)\n❌ ELIMINATED"
                    node_color = "rgba(255, 99, 99, 0.8)"  # Red for eliminated
                else:
                    node_label = f"{candidate_name}\nRound {round_num}\n({vote_count:,} votes)"
                    node_color = candidate_colors[candidate_name]
                
                nodes.append(node_label)
                node_colors.append(node_color)
                node_map[node_key] = node_index
                node_index += 1
    
    # Create links showing vote redistribution from eliminated candidates
    for round_idx, round_result in enumerate(election_result.rounds):
        if round_result.eliminated_candidate and round_result.vote_transfers:
            eliminated = round_result.eliminated_candidate
            eliminated_key = f"{eliminated}_R{round_result.round_number}"
            
            # Create transfer flows from eliminated candidate to receiving candidates
            if eliminated_key in node_map:
                for transfer in round_result.vote_transfers:
                    target_candidate = transfer.to_candidate
                    transfer_votes = transfer.vote_count
                    
                    # For final round, transfers conceptually go to winner (no next round to show)
                    # For other rounds, find the target candidate in the next round
                    target_key = None
                    
                    if round_idx == len(election_result.rounds) - 1:
                        # Final round - transfers determine winner
                        if target_candidate == election_result.winner:
                            # Create winner node if not exists
                            winner_key = f"🏆 {election_result.winner} (Winner)"
                            if winner_key not in node_map:
                                nodes.append(f"🏆 {election_result.winner}\nWINNER")
                                node_colors.append("rgba(255, 215, 0, 0.9)")  # Gold for winner
                                node_map[winner_key] = node_index
                                node_index += 1
                            target_key = winner_key
                    else:
                        # Not final round - link to next round
                        next_round_idx = round_idx + 1
                        if next_round_idx < len(election_result.rounds):
                            next_round = election_result.rounds[next_round_idx]
                            target_key = f"{target_candidate}_R{next_round.round_number}"
                    
                    if target_key and target_key in node_map and transfer_votes > 0:
                        links.append({
                            "source": node_map[eliminated_key],
                            "target": node_map[target_key],
                            "value": transfer_votes,
                            "color": "rgba(255, 100, 100, 0.8)"  # Red for transfers
                        })
            
            # Handle exhausted ballots from eliminated candidate
            eliminated_votes = round_result.vote_counts.get(eliminated, 0)
            total_transferred = sum(t.vote_count for t in round_result.vote_transfers)
            exhausted_from_elimination = eliminated_votes - total_transferred
            
            if exhausted_from_elimination > 0:
                # Add exhausted node if not already created
                exhausted_key = "Exhausted_Ballots"
                if exhausted_key not in node_map:
                    nodes.append(f"Exhausted Ballots\n({exhausted_from_elimination:,} total)")
                    node_colors.append("rgba(128, 128, 128, 0.6)")  # Gray for exhausted
                    node_map[exhausted_key] = node_index
                    node_index += 1
                
                links.append({
                    "source": node_map[eliminated_key],
                    "target": node_map[exhausted_key],
                    "value": exhausted_from_elimination,
                    "color": "rgba(128, 128, 128, 0.5)"  # Gray for exhausted
                })
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=node_colors,
            hovertemplate="<b>%{label}</b><extra></extra>"
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            color=[link["color"] for link in links],
            hovertemplate="<b>%{value:,} votes</b><br>" +
                         "From: %{source.label}<br>" +
                         "To: %{target.label}<extra></extra>"
        )
    )])
    
    # Enhanced layout
    fig.update_layout(
        title={
            "text": f"Complete RCV Vote Flow - {len(election_result.rounds)} Rounds",
            "x": 0.5,
            "font": {"size": 18, "color": "darkblue"}
        },
        font=dict(size=11, family="Arial, sans-serif"),
        height=max(500, len(nodes) * 25 + 200),  # Dynamic height
        margin=dict(l=20, r=20, t=80, b=60),
        plot_bgcolor="rgba(248, 249, 250, 0.8)",
        annotations=[
            dict(
                text="📊 Red flows show vote transfers from eliminated candidates • Gray flows show exhausted ballots",
                xref="paper", yref="paper",
                x=0.5, y=0.02,
                xanchor="center",
                showarrow=False,
                font=dict(size=12, color="darkslategray"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="lightgray",
                borderwidth=1,
                borderpad=8
            )
        ]
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