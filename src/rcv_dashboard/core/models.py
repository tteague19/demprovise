"""Core Pydantic models for RCV election data structures.

This module defines the fundamental data models used throughout the RCV Dashboard
for representing election results, ballot data, and configuration settings.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CandidateInfo(BaseModel):
    """Information about a candidate in an election.
    
    Attributes:
        name: The candidate's name
        status: Current status (active, eliminated, winner)
        elimination_round: Round in which candidate was eliminated (if applicable)
        vote_count: Current vote count for this candidate
    """
    
    name: str = Field(..., min_length=1, description="Candidate name")
    status: str = Field(default="active", description="Current candidate status")
    elimination_round: int | None = Field(
        default=None, ge=1, description="Round eliminated (if applicable)"
    )
    vote_count: int = Field(default=0, ge=0, description="Current vote count")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate candidate status values."""
        allowed_statuses = {"active", "eliminated", "winner"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return v


class VoteTransfer(BaseModel):
    """Details of vote transfers when a candidate is eliminated.
    
    Attributes:
        from_candidate: Candidate whose votes are being transferred
        to_candidate: Candidate receiving the transferred votes
        vote_count: Number of votes transferred
        transfer_round: Round in which transfer occurred
    """
    
    from_candidate: str = Field(..., min_length=1)
    to_candidate: str = Field(..., min_length=1)
    vote_count: int = Field(..., gt=0)
    transfer_round: int = Field(..., gt=0)


class RoundResult(BaseModel):
    """Results for a single round of RCV elimination.
    
    Attributes:
        round_number: The round number (1-based)
        vote_counts: Mapping of candidate names to vote counts
        eliminated_candidate: Candidate eliminated this round (if any)
        vote_transfers: Details of vote transfers from eliminated candidate
        exhausted_ballots: Number of ballots with no remaining valid choices
        total_votes: Total number of active votes this round
    """
    
    round_number: int = Field(..., gt=0)
    vote_counts: dict[str, int] = Field(default_factory=dict)
    eliminated_candidate: str | None = Field(default=None)
    vote_transfers: list[VoteTransfer] = Field(default_factory=list)
    exhausted_ballots: int = Field(default=0, ge=0)
    total_votes: int = Field(..., ge=0)
    
    @field_validator("vote_counts")
    @classmethod
    def validate_vote_counts(cls, v: dict[str, int]) -> dict[str, int]:
        """Ensure all vote counts are non-negative."""
        for candidate, votes in v.items():
            if votes < 0:
                raise ValueError(f"Vote count for {candidate} cannot be negative")
        return v


class ElectionResult(BaseModel):
    """Complete results of an RCV election.
    
    Attributes:
        winner: Name of the winning candidate
        total_ballots: Total number of ballots cast
        rounds: Results for each elimination round
        candidates: Information about all candidates
        majority_threshold: Number of votes needed for majority
        winner_vote_percentage: Winner's final vote percentage
    """
    
    winner: str = Field(..., min_length=1)
    total_ballots: int = Field(..., gt=0)
    rounds: list[RoundResult] = Field(..., min_items=1)
    candidates: list[CandidateInfo] = Field(..., min_items=1)
    majority_threshold: int = Field(..., gt=0)
    winner_vote_percentage: float = Field(..., ge=0.0, le=100.0)
    
    @field_validator("winner_vote_percentage")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentage is reasonable precision."""
        return round(v, 2)


class BallotData(BaseModel):
    """Raw ballot data loaded from files.
    
    Attributes:
        ballots: List of ballots, each ballot is a list of candidate preferences
        candidates: Set of all candidates mentioned in ballots
        total_ballots: Total number of valid ballots
        invalid_ballots: Number of invalid/malformed ballots found
    """
    
    ballots: list[list[str]] = Field(..., min_items=1)
    candidates: set[str] = Field(..., min_items=1)
    total_ballots: int = Field(..., gt=0)
    invalid_ballots: int = Field(default=0, ge=0)
    
    @field_validator("ballots")
    @classmethod
    def validate_ballots(cls, v: list[list[str]]) -> list[list[str]]:
        """Ensure ballots are properly formatted."""
        for i, ballot in enumerate(v):
            if not ballot:
                raise ValueError(f"Ballot {i} is empty")
            # Check for duplicate preferences in single ballot
            cleaned_ballot = [choice for choice in ballot if choice.strip()]
            if len(cleaned_ballot) != len(set(cleaned_ballot)):
                raise ValueError(f"Ballot {i} contains duplicate preferences")
        return v


class ValidationResult(BaseModel):
    """Result of ballot validation process.
    
    Attributes:
        is_valid: Whether the data passed validation
        errors: List of validation error messages
        warnings: List of validation warnings
        candidate_count: Number of unique candidates found
        ballot_count: Number of valid ballots processed
    """
    
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    candidate_count: int = Field(default=0, ge=0)
    ballot_count: int = Field(default=0, ge=0)


class AppSettings(BaseSettings):
    """Application configuration settings using Pydantic Settings.
    
    Settings can be configured via environment variables with APP_ prefix.
    Example: APP_DEBUG=true sets debug=True
    """
    
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    app_name: str = Field(default="RCV Dashboard", description="Application name")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Max upload size in MB")
    
    # Visualization settings
    chart_theme: str = Field(default="plotly", description="Default chart theme")
    chart_height: int = Field(default=500, ge=200, le=1000, description="Default chart height")
    animation_duration: int = Field(default=1000, ge=0, le=5000, description="Animation duration in ms")
    
    # Processing settings
    max_candidates: int = Field(default=50, ge=2, le=100, description="Maximum number of candidates")
    max_ballots: int = Field(default=100000, ge=1, description="Maximum number of ballots")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    
    @field_validator("chart_theme")
    @classmethod
    def validate_chart_theme(cls, v: str) -> str:
        """Validate chart theme options."""
        allowed_themes = {"plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn"}
        if v not in allowed_themes:
            raise ValueError(f"Chart theme must be one of {allowed_themes}")
        return v


class ScenarioInfo(BaseModel):
    """Information about a pre-built election scenario.
    
    Attributes:
        name: Display name for the scenario
        description: Brief description of what the scenario demonstrates
        category: Category (education, demonstration, example)
        ballot_count: Number of ballots in this scenario
        candidate_count: Number of candidates in this scenario
        expected_winner: Expected winner (for educational purposes)
    """
    
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    category: str = Field(default="demonstration")
    ballot_count: int = Field(..., gt=0)
    candidate_count: int = Field(..., gt=1)
    expected_winner: str | None = Field(default=None)
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate scenario category."""
        allowed_categories = {"education", "demonstration", "example", "test"}
        if v not in allowed_categories:
            raise ValueError(f"Category must be one of {allowed_categories}")
        return v