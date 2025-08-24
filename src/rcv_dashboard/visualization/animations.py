"""Animation components for round-by-round RCV visualizations.

This module creates engaging animated visualizations that show the progression
of ranked choice voting rounds, making the elimination process more intuitive.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..core.models import ElectionResult, RoundResult


def create_animated_round_progression(election_result: ElectionResult) -> go.Figure:
    """Create an animated bar chart showing vote progression across rounds.
    
    Creates a dynamic visualization where each frame shows one round of the
    election, with bars growing/shrinking as votes are transferred and
    candidates eliminated.
    
    Args:
        election_result: Complete election results with all rounds
        
    Returns:
        Plotly figure with animation frames for each round
        
    Examples:
        >>> from src.rcv_dashboard.core.models import ElectionResult, RoundResult, CandidateInfo
        >>> candidates = [
        ...     CandidateInfo(name="Alice", vote_count=100),
        ...     CandidateInfo(name="Bob", vote_count=80)
        ... ]
        >>> rounds = [
        ...     RoundResult(round_number=1, vote_counts={"Alice": 100, "Bob": 80}, 
        ...                eliminated_candidate=None, winner=None, total_votes=180)
        ... ]
        >>> result = ElectionResult(winner="Alice", total_rounds=1, candidates=candidates,
        ...                        rounds=rounds, total_ballots=180)
        >>> fig = create_animated_round_progression(result)
        >>> fig.data[0].type == 'bar'
        True
    """
    if not election_result.rounds:
        # Create empty figure if no rounds
        fig = go.Figure()
        fig.update_layout(
            title="No Election Data Available",
            xaxis_title="Candidates",
            yaxis_title="Votes"
        )
        return fig
    
    # Collect all candidates across all rounds
    all_candidates = set()
    for round_result in election_result.rounds:
        all_candidates.update(round_result.vote_counts.keys())
    candidates_list = sorted(all_candidates)
    
    # Define colors for candidates
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    candidate_colors = {
        candidate: colors[i % len(colors)] 
        for i, candidate in enumerate(candidates_list)
    }
    
    # Create frames for each round
    frames = []
    for i, round_result in enumerate(election_result.rounds):
        vote_counts = round_result.vote_counts
        eliminated = round_result.eliminated_candidate
        
        # Prepare data for this round
        candidates_in_round = []
        votes_in_round = []
        colors_in_round = []
        
        for candidate in candidates_list:
            if candidate in vote_counts:
                candidates_in_round.append(candidate)
                votes_in_round.append(vote_counts[candidate])
                
                # Use different opacity for eliminated candidates
                if eliminated and candidate == eliminated:
                    # Dimmed color for eliminated candidate
                    base_color = candidate_colors[candidate]
                    colors_in_round.append(f'rgba({",".join(str(int(base_color[j:j+2], 16)) for j in (1, 3, 5))}, 0.3)')
                else:
                    colors_in_round.append(candidate_colors[candidate])
        
        # Create frame
        frame_title = f"Round {round_result.round_number}"
        if eliminated:
            frame_title += f" - {eliminated} Eliminated"
        elif round_result.winner:
            frame_title += f" - {round_result.winner} Wins!"
            
        frame = go.Frame(
            data=[
                go.Bar(
                    x=candidates_in_round,
                    y=votes_in_round,
                    marker_color=colors_in_round,
                    text=[f"{votes:,}" for votes in votes_in_round],
                    textposition="outside",
                    name=frame_title
                )
            ],
            name=str(i),
            layout=go.Layout(title_text=frame_title)
        )
        frames.append(frame)
    
    # Create initial figure with first round
    first_round = election_result.rounds[0]
    initial_candidates = list(first_round.vote_counts.keys())
    initial_votes = list(first_round.vote_counts.values())
    initial_colors = [candidate_colors[c] for c in initial_candidates]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=initial_candidates,
                y=initial_votes,
                marker_color=initial_colors,
                text=[f"{votes:,}" for votes in initial_votes],
                textposition="outside"
            )
        ],
        frames=frames
    )
    
    # Add animation controls
    fig.update_layout(
        title={
            'text': f"RCV Election Animation - {election_result.total_rounds} Rounds",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Candidates",
        yaxis_title="Vote Count",
        showlegend=False,
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {
                    'label': '▶ Play',
                    'method': 'animate',
                    'args': [
                        None,
                        {
                            'frame': {'duration': 2000, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 500}
                        }
                    ]
                },
                {
                    'label': '⏸ Pause', 
                    'method': 'animate',
                    'args': [
                        [None],
                        {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }
                    ]
                }
            ]
        }],
        sliders=[{
            'active': 0,
            'steps': [
                {
                    'args': [
                        [str(i)],
                        {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }
                    ],
                    'label': f"Round {i+1}",
                    'method': 'animate'
                }
                for i in range(len(election_result.rounds))
            ],
            'currentvalue': {'prefix': 'Round: '},
            'len': 0.8,
            'x': 0.1,
            'y': 0
        }]
    )
    
    return fig


def create_vote_flow_animation(election_result: ElectionResult) -> go.Figure:
    """Create an animated visualization showing vote transfers.
    
    Shows how votes flow from eliminated candidates to remaining ones,
    using animated arrows or flow diagrams.
    
    Args:
        election_result: Complete election results with transfer data
        
    Returns:
        Plotly figure with vote transfer animations
    """
    if not election_result.rounds or len(election_result.rounds) < 2:
        fig = go.Figure()
        fig.update_layout(
            title="No Vote Transfers to Animate",
            annotations=[{
                'text': 'Need at least 2 rounds to show vote transfers',
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': 0.5, 'showarrow': False,
                'font': {'size': 16}
            }]
        )
        return fig
    
    # This is a simplified version - would need more complex logic for full transfer animation
    return create_animated_round_progression(election_result)


def create_elimination_timeline(election_result: ElectionResult) -> go.Figure:
    """Create an animated timeline showing when each candidate is eliminated.
    
    Displays a timeline view where candidates are progressively eliminated,
    showing the order and timing of eliminations.
    
    Args:
        election_result: Complete election results 
        
    Returns:
        Plotly figure with elimination timeline animation
    """
    if not election_result.candidates:
        fig = go.Figure()
        fig.update_layout(title="No Candidates to Display")
        return fig
    
    # Extract elimination data
    eliminations = []
    winner = None
    
    for round_result in election_result.rounds:
        if round_result.eliminated_candidate:
            eliminations.append({
                'candidate': round_result.eliminated_candidate,
                'round': round_result.round_number,
                'final_votes': round_result.vote_counts.get(round_result.eliminated_candidate, 0)
            })
        if round_result.winner:
            winner = round_result.winner
    
    # Add winner to the end
    if winner:
        final_round = election_result.rounds[-1]
        winner_votes = final_round.vote_counts.get(winner, 0)
        eliminations.append({
            'candidate': winner,
            'round': final_round.round_number,
            'final_votes': winner_votes,
            'is_winner': True
        })
    
    if not eliminations:
        fig = go.Figure()
        fig.update_layout(title="No Elimination Data Available")
        return fig
    
    # Create timeline visualization
    fig = go.Figure()
    
    rounds = [item['round'] for item in eliminations]
    candidates = [item['candidate'] for item in eliminations]
    votes = [item['final_votes'] for item in eliminations]
    
    # Different colors for eliminated vs winner
    colors = ['red' if not item.get('is_winner', False) else 'gold' for item in eliminations]
    symbols = ['x' if not item.get('is_winner', False) else 'star' for item in eliminations]
    
    fig.add_trace(go.Scatter(
        x=rounds,
        y=candidates,
        mode='markers+text',
        marker=dict(
            size=15,
            color=colors,
            symbol=symbols,
            line=dict(width=2, color='black')
        ),
        text=[f"{votes:,} votes" for votes in votes],
        textposition="middle right",
        hovertemplate="<b>%{y}</b><br>Round %{x}<br>Final Votes: %{text}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Candidate Elimination Timeline",
        xaxis_title="Round",
        yaxis_title="Candidates",
        xaxis=dict(tick0=1, dtick=1),
        showlegend=False,
        height=400 + len(eliminations) * 30  # Dynamic height based on candidates
    )
    
    return fig


def create_majority_threshold_animation(election_result: ElectionResult) -> go.Figure:
    """Create animation showing progress toward majority threshold.
    
    Shows a horizontal line representing the majority threshold and animates
    how candidates approach or exceed this threshold across rounds.
    
    Args:
        election_result: Complete election results
        
    Returns:
        Plotly figure with majority threshold animation
    """
    if not election_result.rounds:
        fig = go.Figure()
        fig.update_layout(title="No Election Data Available")
        return fig
    
    # Calculate majority threshold for each round
    frames = []
    all_candidates = set()
    
    for round_result in election_result.rounds:
        all_candidates.update(round_result.vote_counts.keys())
    
    candidates_list = sorted(all_candidates)
    
    for i, round_result in enumerate(election_result.rounds):
        majority_threshold = round_result.total_votes / 2
        
        candidates_in_round = []
        votes_in_round = []
        colors_in_round = []
        
        for candidate in candidates_list:
            if candidate in round_result.vote_counts:
                votes = round_result.vote_counts[candidate]
                candidates_in_round.append(candidate)
                votes_in_round.append(votes)
                
                # Color based on majority status
                if votes > majority_threshold:
                    colors_in_round.append('green')  # Has majority
                else:
                    colors_in_round.append('lightblue')  # No majority
        
        # Create frame
        frame = go.Frame(
            data=[
                go.Bar(
                    x=candidates_in_round,
                    y=votes_in_round,
                    marker_color=colors_in_round,
                    text=[f"{votes:,}" for votes in votes_in_round],
                    textposition="outside"
                ),
                go.Scatter(
                    x=candidates_in_round,
                    y=[majority_threshold] * len(candidates_in_round),
                    mode='lines',
                    line=dict(color='red', dash='dash', width=2),
                    name=f"Majority Threshold ({majority_threshold:,.0f})"
                )
            ],
            name=str(i),
            layout=go.Layout(
                title_text=f"Round {round_result.round_number} - Majority Threshold: {majority_threshold:,.0f}"
            )
        )
        frames.append(frame)
    
    # Initial figure
    first_round = election_result.rounds[0]
    initial_threshold = first_round.total_votes / 2
    initial_candidates = list(first_round.vote_counts.keys())
    initial_votes = list(first_round.vote_counts.values())
    initial_colors = ['green' if v > initial_threshold else 'lightblue' for v in initial_votes]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=initial_candidates,
                y=initial_votes,
                marker_color=initial_colors,
                text=[f"{votes:,}" for votes in initial_votes],
                textposition="outside"
            ),
            go.Scatter(
                x=initial_candidates,
                y=[initial_threshold] * len(initial_candidates),
                mode='lines',
                line=dict(color='red', dash='dash', width=2),
                name=f"Majority Threshold"
            )
        ],
        frames=frames
    )
    
    fig.update_layout(
        title="Progress Toward Majority Threshold",
        xaxis_title="Candidates",
        yaxis_title="Votes",
        showlegend=True
    )
    
    return fig