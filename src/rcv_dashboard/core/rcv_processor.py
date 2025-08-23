"""Core RCV processing algorithm implementation.

This module implements the ranked choice voting algorithm using Pydantic models
for data validation and type safety.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

from .models import (
    BallotData,
    CandidateInfo,
    ElectionResult,
    RoundResult,
    VoteTransfer,
)


class RCVProcessor:
    """Processes ranked choice voting elections with comprehensive validation.
    
    This class implements the standard RCV algorithm:
    1. Count first-choice votes for each candidate
    2. If any candidate has a majority, they win
    3. Otherwise, eliminate the candidate with the fewest votes
    4. Transfer their votes to the next choice on each ballot
    5. Repeat until someone has a majority or only one candidate remains
    
    Example:
        >>> ballots = [["Alice", "Bob"], ["Bob", "Alice"], ["Alice"]]
        >>> processor = RCVProcessor(BallotData(
        ...     ballots=ballots,
        ...     candidates={"Alice", "Bob"},
        ...     total_ballots=3,
        ... ))
        >>> result = processor.run_election()
        >>> result.winner
        'Alice'
    """
    
    def __init__(self, ballot_data: BallotData) -> None:
        """Initialize the RCV processor with validated ballot data.
        
        Args:
            ballot_data: Validated ballot data containing all ballots and candidates
        """
        self.ballot_data = ballot_data
        self.active_ballots = [ballot.copy() for ballot in ballot_data.ballots]
        self.active_candidates = set(ballot_data.candidates)
        self.eliminated_candidates: list[str] = []
        self.rounds: list[RoundResult] = []
    
    def run_election(self) -> ElectionResult:
        """Run the complete RCV election and return results.
        
        Returns:
            Complete election results including all rounds and winner
            
        Raises:
            ValueError: If no valid candidates remain or other election errors
        """
        if len(self.active_candidates) < 1:
            raise ValueError("No candidates available for election")
        
        if len(self.active_candidates) == 1:
            # Single candidate - automatic winner
            winner = next(iter(self.active_candidates))
            return self._create_single_candidate_result(winner)
        
        round_number = 1
        majority_threshold = (self.ballot_data.total_ballots // 2) + 1
        
        while len(self.active_candidates) > 1:
            # Count votes for current round
            vote_counts = self._count_votes()
            
            # Check for majority winner
            max_votes = max(vote_counts.values()) if vote_counts else 0
            if max_votes >= majority_threshold:
                winner = self._get_candidate_with_most_votes(vote_counts)
                self._add_round(round_number, vote_counts, None)
                break
            
            # Find candidate to eliminate
            candidate_to_eliminate = self._get_candidate_with_fewest_votes(vote_counts)
            
            # Transfer votes from eliminated candidate
            vote_transfers = self._transfer_votes(candidate_to_eliminate)
            
            # Record this round's results
            self._add_round(round_number, vote_counts, candidate_to_eliminate, vote_transfers)
            
            # Remove eliminated candidate
            self.active_candidates.remove(candidate_to_eliminate)
            self.eliminated_candidates.append(candidate_to_eliminate)
            
            round_number += 1
            
            # Safety check to prevent infinite loops
            if round_number > len(self.ballot_data.candidates):
                raise ValueError("Election processing exceeded maximum rounds")
        
        # Determine final winner
        if len(self.active_candidates) == 1:
            winner = next(iter(self.active_candidates))
        else:
            final_counts = self._count_votes()
            winner = self._get_candidate_with_most_votes(final_counts)
        
        return self._create_election_result(winner, majority_threshold)
    
    def _count_votes(self) -> dict[str, int]:
        """Count first-choice votes for all active candidates.
        
        Returns:
            Dictionary mapping candidate names to vote counts
        """
        vote_counts: dict[str, int] = {candidate: 0 for candidate in self.active_candidates}
        
        for ballot in self.active_ballots:
            # Find first active candidate on this ballot
            for candidate in ballot:
                if candidate in self.active_candidates:
                    vote_counts[candidate] += 1
                    break
        
        return vote_counts
    
    def _get_candidate_with_fewest_votes(self, vote_counts: dict[str, int]) -> str:
        """Find the candidate with the fewest votes for elimination.
        
        Args:
            vote_counts: Current vote counts for all candidates
            
        Returns:
            Name of candidate to eliminate
            
        Note:
            In case of ties, eliminates the candidate that appears last alphabetically
            for more interesting elections (avoids always eliminating A's)
        """
        if not vote_counts:
            raise ValueError("No vote counts available for elimination")
        
        min_votes = min(vote_counts.values())
        candidates_with_min = [
            candidate for candidate, votes in vote_counts.items() 
            if votes == min_votes
        ]
        
        # Break ties by taking the last candidate alphabetically for variety
        return sorted(candidates_with_min)[-1]
    
    def _get_candidate_with_most_votes(self, vote_counts: dict[str, int]) -> str:
        """Find the candidate with the most votes.
        
        Args:
            vote_counts: Current vote counts for all candidates
            
        Returns:
            Name of winning candidate
        """
        if not vote_counts:
            raise ValueError("No vote counts available")
        
        max_votes = max(vote_counts.values())
        candidates_with_max = [
            candidate for candidate, votes in vote_counts.items()
            if votes == max_votes
        ]
        
        # In case of tie, return first alphabetically
        return sorted(candidates_with_max)[0]
    
    def _transfer_votes(self, eliminated_candidate: str) -> list[VoteTransfer]:
        """Transfer votes from eliminated candidate to next choices.
        
        Args:
            eliminated_candidate: Candidate being eliminated
            
        Returns:
            List of vote transfer details
        """
        transfer_counts: dict[str, int] = defaultdict(int)
        exhausted_count = 0
        
        # Process each ballot
        for ballot in self.active_ballots:
            if ballot and ballot[0] == eliminated_candidate:
                # Remove the eliminated candidate from this ballot
                ballot.remove(eliminated_candidate)
                
                # Find next active candidate
                transferred = False
                for candidate in ballot:
                    if candidate in self.active_candidates:
                        transfer_counts[candidate] += 1
                        transferred = True
                        break
                
                if not transferred:
                    exhausted_count += 1
        
        # Create transfer objects
        transfers = [
            VoteTransfer(
                from_candidate=eliminated_candidate,
                to_candidate=to_candidate,
                vote_count=count,
                transfer_round=len(self.rounds) + 1
            )
            for to_candidate, count in transfer_counts.items()
        ]
        
        return transfers
    
    def _add_round(
        self,
        round_number: int,
        vote_counts: dict[str, int],
        eliminated_candidate: str | None,
        vote_transfers: list[VoteTransfer] | None = None,
    ) -> None:
        """Add a round's results to the election record.
        
        Args:
            round_number: The round number
            vote_counts: Vote counts for this round
            eliminated_candidate: Candidate eliminated (if any)
            vote_transfers: Vote transfer details (if any)
        """
        total_votes = sum(vote_counts.values())
        exhausted_ballots = self.ballot_data.total_ballots - total_votes
        
        round_result = RoundResult(
            round_number=round_number,
            vote_counts=vote_counts.copy(),
            eliminated_candidate=eliminated_candidate,
            vote_transfers=vote_transfers or [],
            exhausted_ballots=exhausted_ballots,
            total_votes=total_votes,
        )
        
        self.rounds.append(round_result)
    
    def _create_election_result(self, winner: str, majority_threshold: int) -> ElectionResult:
        """Create the final election result object.
        
        Args:
            winner: Name of the winning candidate
            majority_threshold: Votes needed for majority
            
        Returns:
            Complete election results
        """
        # Create candidate info objects
        candidates = []
        for candidate_name in self.ballot_data.candidates:
            if candidate_name == winner:
                status = "winner"
                elimination_round = None
            elif candidate_name in self.eliminated_candidates:
                status = "eliminated"
                # Find elimination round
                elimination_round = None
                for round_result in self.rounds:
                    if round_result.eliminated_candidate == candidate_name:
                        elimination_round = round_result.round_number
                        break
            else:
                status = "active"
                elimination_round = None
            
            # Get final vote count
            final_votes = 0
            if self.rounds:
                final_round = self.rounds[-1]
                final_votes = final_round.vote_counts.get(candidate_name, 0)
            
            candidate_info = CandidateInfo(
                name=candidate_name,
                status=status,
                elimination_round=elimination_round,
                vote_count=final_votes,
            )
            candidates.append(candidate_info)
        
        # Calculate winner percentage
        winner_votes = 0
        if self.rounds:
            winner_votes = self.rounds[-1].vote_counts.get(winner, 0)
        
        winner_percentage = (
            (winner_votes / self.ballot_data.total_ballots) * 100.0
            if self.ballot_data.total_ballots > 0 else 0.0
        )
        
        return ElectionResult(
            winner=winner,
            total_ballots=self.ballot_data.total_ballots,
            rounds=self.rounds.copy(),
            candidates=candidates,
            majority_threshold=majority_threshold,
            winner_vote_percentage=winner_percentage,
        )
    
    def _create_single_candidate_result(self, winner: str) -> ElectionResult:
        """Create result for election with single candidate.
        
        Args:
            winner: The only candidate
            
        Returns:
            Election result with single round
        """
        candidate_info = CandidateInfo(
            name=winner,
            status="winner",
            vote_count=self.ballot_data.total_ballots,
        )
        
        round_result = RoundResult(
            round_number=1,
            vote_counts={winner: self.ballot_data.total_ballots},
            total_votes=self.ballot_data.total_ballots,
        )
        
        return ElectionResult(
            winner=winner,
            total_ballots=self.ballot_data.total_ballots,
            rounds=[round_result],
            candidates=[candidate_info],
            majority_threshold=1,
            winner_vote_percentage=100.0,
        )
    
    def get_round_details(self, round_num: int) -> RoundResult:
        """Get detailed results for a specific round.
        
        Args:
            round_num: Round number (1-based)
            
        Returns:
            Results for the specified round
            
        Raises:
            ValueError: If round number is invalid
        """
        if round_num < 1 or round_num > len(self.rounds):
            raise ValueError(f"Invalid round number: {round_num}")
        
        return self.rounds[round_num - 1]
    
    def get_elimination_order(self) -> list[str]:
        """Get the order in which candidates were eliminated.
        
        Returns:
            List of candidate names in elimination order
        """
        return self.eliminated_candidates.copy()
    
    def get_vote_transfers(self, eliminated_candidate: str) -> dict[str, int]:
        """Get vote transfer details for a specific eliminated candidate.
        
        Args:
            eliminated_candidate: Name of eliminated candidate
            
        Returns:
            Dictionary mapping receiving candidates to transfer counts
            
        Raises:
            ValueError: If candidate was not eliminated
        """
        if eliminated_candidate not in self.eliminated_candidates:
            raise ValueError(f"Candidate {eliminated_candidate} was not eliminated")
        
        transfers: dict[str, int] = {}
        for round_result in self.rounds:
            if round_result.eliminated_candidate == eliminated_candidate:
                for transfer in round_result.vote_transfers:
                    transfers[transfer.to_candidate] = transfer.vote_count
                break
        
        return transfers