"""Pre-built election scenarios for educational demonstration.

This module provides a collection of carefully crafted election scenarios
that illustrate key RCV concepts like spoiler effects, consensus winners,
and multi-round eliminations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..core.models import BallotData


@dataclass(frozen=True)
class ScenarioInfo:
    """Information about a demonstration scenario.
    
    Attributes:
        name: Human-readable scenario name
        description: Brief explanation of what this scenario demonstrates
        educational_point: Key RCV concept illustrated
        candidate_count: Number of candidates in this scenario
        ballot_count: Number of ballots in this scenario
        expected_winner: Who should win under RCV (for verification)
        expected_rounds: Expected number of elimination rounds
    """
    name: str
    description: str
    educational_point: str
    candidate_count: int
    ballot_count: int
    expected_winner: str
    expected_rounds: int


def get_scenario_list() -> Sequence[ScenarioInfo]:
    """Get list of all available demonstration scenarios.
    
    Returns:
        Sequence of scenario information objects
        
    Example:
        >>> scenarios = get_scenario_list()
        >>> print(f"Available scenarios: {len(scenarios)}")
        Available scenarios: 7
    """
    return [
        ScenarioInfo(
            name="Classic Spoiler Effect",
            description="Shows how RCV prevents spoiler candidates from changing the outcome",
            educational_point="Spoiler Prevention",
            candidate_count=3,
            ballot_count=100,
            expected_winner="Moderate Candidate",
            expected_rounds=2
        ),
        ScenarioInfo(
            name="Polarized vs Consensus",
            description="Demonstrates how RCV can elect a consensus candidate over a polarizing one",
            educational_point="Consensus Building", 
            candidate_count=3,
            ballot_count=90,
            expected_winner="Consensus Builder",
            expected_rounds=2
        ),
        ScenarioInfo(
            name="Close Three-Way Race",
            description="Multi-round elimination with tight competition between three candidates",
            educational_point="Multi-Round Eliminations",
            candidate_count=3,
            ballot_count=120,
            expected_winner="Gradual Gainer",
            expected_rounds=2
        ),
        ScenarioInfo(
            name="Landslide Victory",
            description="Clear majority winner decided in the first round",
            educational_point="First-Round Majority",
            candidate_count=4,
            ballot_count=80,
            expected_winner="Popular Choice",
            expected_rounds=1
        ),
        ScenarioInfo(
            name="Comedy Competition",
            description="Themed scenario around different comedy performance styles",
            educational_point="Thematic Application",
            candidate_count=4,
            ballot_count=150,
            expected_winner="Improv Ace",
            expected_rounds=3
        ),
        ScenarioInfo(
            name="Student Government",
            description="Academic election with platform-based voting patterns",
            educational_point="Issue-Based Voting",
            candidate_count=3,
            ballot_count=200,
            expected_winner="Sarah Martinez",
            expected_rounds=2
        ),
        ScenarioInfo(
            name="City Council Race",
            description="Municipal election with neighborhood-based voting patterns",
            educational_point="Geographic Coalitions",
            candidate_count=4,
            ballot_count=300,
            expected_winner="Maria Rodriguez",
            expected_rounds=3
        ),
    ]


def load_scenario(scenario_name: str) -> tuple[BallotData, str, str]:
    """Load a specific demonstration scenario.
    
    Args:
        scenario_name: Name of the scenario to load
        
    Returns:
        Tuple of (ballot_data, detailed_description, analysis_notes)
        
    Raises:
        ValueError: If scenario name is not found
        
    Example:
        >>> ballot_data, description, notes = load_scenario("Classic Spoiler Effect")
        >>> print(f"Loaded {ballot_data.total_ballots} ballots")
        Loaded 100 ballots
    """
    scenario_functions = {
        "Classic Spoiler Effect": _create_spoiler_effect_scenario,
        "Polarized vs Consensus": _create_polarized_vs_consensus_scenario,
        "Close Three-Way Race": _create_close_three_way_scenario,
        "Landslide Victory": _create_landslide_victory_scenario,
        "Comedy Competition": _create_comedy_competition_scenario,
        "Student Government": _create_student_government_scenario,
        "City Council Race": _create_city_council_scenario,
    }
    
    if scenario_name not in scenario_functions:
        available = ", ".join(scenario_functions.keys())
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {available}")
    
    return scenario_functions[scenario_name]()


def _create_spoiler_effect_scenario() -> tuple[BallotData, str, str]:
    """Create the classic spoiler effect demonstration."""
    ballots = []
    
    # Progressive voters (40%) - prefer Liberal, would accept Moderate over Conservative
    for _ in range(40):
        ballots.append(["Liberal Candidate", "Moderate Candidate", "Conservative Candidate"])
    
    # Conservative voters (35%) - prefer Conservative, would accept Moderate over Liberal  
    for _ in range(35):
        ballots.append(["Conservative Candidate", "Moderate Candidate", "Liberal Candidate"])
    
    # Moderate voters (25%) - prefer Moderate, split second choices
    for _ in range(15):
        ballots.append(["Moderate Candidate", "Liberal Candidate", "Conservative Candidate"])
    for _ in range(10):
        ballots.append(["Moderate Candidate", "Conservative Candidate", "Liberal Candidate"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Liberal Candidate", "Moderate Candidate", "Conservative Candidate"},
        total_ballots=len(ballots)
    )
    
    description = """
    **The Classic Spoiler Effect Scenario**
    
    This scenario demonstrates how RCV prevents the "spoiler effect" that can occur in 
    plurality voting systems. In a traditional election, the Liberal and Conservative 
    candidates might split the vote, allowing an unintended winner.
    
    **Voter Breakdown:**
    - 40% Progressive voters (Liberal → Moderate → Conservative)
    - 35% Conservative voters (Conservative → Moderate → Liberal)
    - 25% Moderate voters (Moderate → mixed second choices)
    
    **In Plurality Voting:** Liberal would win with 40% despite being opposed by 60%
    **In RCV:** The candidate with broadest support wins through elimination rounds
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Spoiler Prevention:** No candidate can "steal" votes and change the outcome
    2. **Majority Support:** The winner will have majority support from voters
    3. **Vote Transfers:** Watch how second choices matter when first choices are eliminated
    4. **Centrist Appeal:** Moderate positions often gain support through transfers
    """
    
    return ballot_data, description, analysis


def _create_polarized_vs_consensus_scenario() -> tuple[BallotData, str, str]:
    """Create polarized vs consensus candidate demonstration."""
    ballots = []
    
    # Polarizing candidate has strong first-choice support but few second choices
    # Base voters (30%) - strongly prefer Polarizing candidate
    for _ in range(27):
        ballots.append(["Polarizing Leader", "Consensus Builder", "Moderate Alternative"])
    for _ in range(3):
        ballots.append(["Polarizing Leader", "Moderate Alternative", "Consensus Builder"])
    
    # Consensus candidate has moderate first-choice but is everyone's second choice
    # Direct supporters (25%)
    for _ in range(25):
        ballots.append(["Consensus Builder", "Moderate Alternative", "Polarizing Leader"])
    
    # Moderate alternative supporters (20%) - but they prefer consensus over polarizing
    for _ in range(20):
        ballots.append(["Moderate Alternative", "Consensus Builder", "Polarizing Leader"])
    
    # Voters who dislike the polarizing candidate strongly (25%)
    for _ in range(15):
        ballots.append(["Consensus Builder", "Moderate Alternative"])  # No third choice
    for _ in range(10):
        ballots.append(["Moderate Alternative", "Consensus Builder"])  # No third choice
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Polarizing Leader", "Consensus Builder", "Moderate Alternative"},
        total_ballots=len(ballots)
    )
    
    description = """
    **Polarized vs Consensus Scenario**
    
    This scenario shows how RCV can elect a consensus candidate who has broad appeal
    even when they don't have the most first-choice votes initially.
    
    **Candidate Profiles:**
    - **Polarizing Leader:** Strong base (30%) but divisive - few second-choice votes
    - **Consensus Builder:** Moderate first-choice support (25%) but widely acceptable
    - **Moderate Alternative:** Some direct support (20%) but eliminates first
    
    **The Key Question:** Should the candidate with the most passionate supporters win,
    or the candidate acceptable to the broadest coalition?
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Consensus vs Polarization:** RCV rewards candidates who can build broad coalitions
    2. **Second-Choice Impact:** Being many voters' second choice can lead to victory
    3. **Electability:** Candidates who are "everyone's enemy" struggle in RCV
    4. **Democratic Legitimacy:** Winner has majority support even if not most first choices
    """
    
    return ballot_data, description, analysis


def _create_close_three_way_scenario() -> tuple[BallotData, str, str]:
    """Create a close three-way race with multiple eliminations."""
    ballots = []
    
    # Early Leader voters (35%) - strong in first round but plateaus
    for _ in range(35):
        ballots.append(["Early Leader", "Steady Performer", "Gradual Gainer"])
    
    # Steady Performer voters (30%) - consistent but not enough
    for _ in range(30):
        ballots.append(["Steady Performer", "Gradual Gainer", "Early Leader"])
    
    # Gradual Gainer voters (35%) - few first choices but many second/third
    for _ in range(20):
        ballots.append(["Gradual Gainer", "Steady Performer", "Early Leader"])
    
    # Split voters who help decide through transfers
    for _ in range(25):
        ballots.append(["Early Leader", "Gradual Gainer", "Steady Performer"])
    
    for _ in range(30):
        ballots.append(["Steady Performer", "Early Leader", "Gradual Gainer"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Early Leader", "Steady Performer", "Gradual Gainer"},
        total_ballots=len(ballots)
    )
    
    description = """
    **Close Three-Way Race**
    
    A competitive election where the outcome isn't clear until the final round.
    Each candidate has different strengths and the winner emerges through vote transfers.
    
    **Candidate Profiles:**
    - **Early Leader:** Strong first-choice support but limited growth potential
    - **Steady Performer:** Consistent across rounds but not enough to win
    - **Gradual Gainer:** Fewer first choices but picks up transfers effectively
    
    **Watch for:** How vote transfers can completely change the outcome from first-round results.
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Transfer Strategy:** Being voters' backup choice is crucial
    2. **Round-by-Round Dynamics:** Early leaders don't always win
    3. **Coalition Building:** Success requires appealing beyond your base
    4. **Momentum Changes:** Vote transfers can create surprising comebacks
    """
    
    return ballot_data, description, analysis


def _create_landslide_victory_scenario() -> tuple[BallotData, str, str]:
    """Create a clear majority winner scenario."""
    ballots = []
    
    # Popular Choice has clear majority (55%)
    for _ in range(44):
        ballots.append(["Popular Choice", "Second Place", "Third Place", "Fourth Place"])
    
    # Second Place voters (25%)  
    for _ in range(20):
        ballots.append(["Second Place", "Popular Choice", "Third Place", "Fourth Place"])
    
    # Third Place voters (15%)
    for _ in range(12):
        ballots.append(["Third Place", "Popular Choice", "Second Place", "Fourth Place"])
    
    # Fourth Place voters (5%)
    for _ in range(4):
        ballots.append(["Fourth Place", "Popular Choice", "Second Place", "Third Place"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Popular Choice", "Second Place", "Third Place", "Fourth Place"},
        total_ballots=len(ballots)
    )
    
    description = """
    **Landslide Victory Scenario**
    
    Sometimes RCV elections are decided in the first round when a candidate receives
    a clear majority of first-choice votes. This scenario demonstrates that outcome.
    
    **Results Preview:**
    - **Popular Choice:** Clear majority (55%) wins immediately
    - **Second Place:** Solid support (25%) but not enough
    - **Third Place:** Some support (15%) but distant
    - **Fourth Place:** Minimal support (5%)
    
    **Key Point:** RCV doesn't always require multiple rounds - sometimes voters' 
    preferences are clear from the start.
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **First-Round Wins:** RCV can produce immediate winners with majority support
    2. **Efficiency:** No need for runoffs when preferences are clear
    3. **Mandate Strength:** Winner has clear democratic mandate
    4. **System Flexibility:** RCV works for both close and decisive elections
    """
    
    return ballot_data, description, analysis


def _create_comedy_competition_scenario() -> tuple[BallotData, str, str]:
    """Create a themed comedy performance competition."""
    ballots = []
    
    # Improv fans (35%) - prefer spontaneous, collaborative comedy
    for _ in range(25):
        ballots.append(["Improv Ace", "Sketch Master", "Stand-up Star", "Musical Comic"])
    for _ in range(15):
        ballots.append(["Improv Ace", "Musical Comic", "Sketch Master", "Stand-up Star"])
    for _ in range(10):
        ballots.append(["Improv Ace", "Stand-up Star", "Musical Comic", "Sketch Master"])
    
    # Stand-up fans (30%) - prefer individual comedic storytelling
    for _ in range(30):
        ballots.append(["Stand-up Star", "Improv Ace", "Sketch Master", "Musical Comic"])
    for _ in range(15):
        ballots.append(["Stand-up Star", "Musical Comic", "Improv Ace", "Sketch Master"])
    
    # Sketch fans (20%) - prefer structured, written comedy
    for _ in range(20):
        ballots.append(["Sketch Master", "Musical Comic", "Stand-up Star", "Improv Ace"])
    for _ in range(10):
        ballots.append(["Sketch Master", "Improv Ace", "Musical Comic", "Stand-up Star"])
    
    # Musical comedy fans (15%) - prefer songs and musical performance
    for _ in range(15):
        ballots.append(["Musical Comic", "Improv Ace", "Sketch Master", "Stand-up Star"])
    for _ in range(10):
        ballots.append(["Musical Comic", "Stand-up Star", "Improv Ace", "Sketch Master"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Improv Ace", "Stand-up Star", "Sketch Master", "Musical Comic"},
        total_ballots=len(ballots)
    )
    
    description = """
    **Comedy Competition Scenario**
    
    A themed election for "Best Comedian" with different comedy styles competing.
    This scenario shows how RCV works with real-world preferences and taste differences.
    
    **Contestant Profiles:**
    - **Improv Ace:** Spontaneous, collaborative comedy style
    - **Stand-up Star:** Individual storytelling and observational humor  
    - **Sketch Master:** Structured, written comedy performances
    - **Musical Comic:** Songs, parodies, and musical comedy acts
    
    **Audience Breakdown:** Each style has dedicated fans, but voters appreciate
    multiple forms of comedy and rank them by preference.
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Taste Preferences:** Different artistic styles create natural voter blocs
    2. **Crossover Appeal:** Some performers appeal across multiple audience types
    3. **Artistic Merit:** Quality can transcend style preferences
    4. **Community Choice:** RCV helps find the performer with broadest community support
    
    **Real-World Application:** This mirrors how RCV works in arts competitions,
    talent shows, and creative contests where subjective preferences matter.
    """
    
    return ballot_data, description, analysis


def _create_student_government_scenario() -> tuple[BallotData, str, str]:
    """Create a student government election scenario."""
    ballots = []
    
    # Academic-focused students (35%) - care about study spaces, library hours
    for _ in range(50):
        ballots.append(["Sarah Martinez", "David Kim", "Alex Thompson"])
    for _ in range(20):
        ballots.append(["Sarah Martinez", "Alex Thompson", "David Kim"])
    
    # Social life focused students (30%) - care about events, clubs, campus life
    for _ in range(40):
        ballots.append(["David Kim", "Alex Thompson", "Sarah Martinez"])
    for _ in range(20):
        ballots.append(["David Kim", "Sarah Martinez", "Alex Thompson"])
    
    # Facilities/practical focused students (35%) - care about parking, food, wifi
    for _ in range(45):
        ballots.append(["Alex Thompson", "Sarah Martinez", "David Kim"])
    for _ in range(25):
        ballots.append(["Alex Thompson", "David Kim", "Sarah Martinez"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"Sarah Martinez", "David Kim", "Alex Thompson"},
        total_ballots=len(ballots)
    )
    
    description = """
    **Student Government Election**
    
    A university student government election with candidates focusing on different
    aspects of campus life. Shows how RCV works with issue-based voting patterns.
    
    **Candidate Platforms:**
    - **Sarah Martinez:** Academic focus - library hours, study spaces, tutoring programs
    - **David Kim:** Social focus - events, clubs, campus traditions, student activities  
    - **Alex Thompson:** Practical focus - parking, dining, WiFi, campus facilities
    
    **Voter Groups:**
    - Students prioritizing academics (35%)
    - Students prioritizing social life (30%)  
    - Students prioritizing practical campus issues (35%)
    
    Each group has a preferred candidate but acceptable alternatives.
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Issue-Based Voting:** Voters group around policy priorities
    2. **Platform Appeal:** Candidates need broad platform appeal beyond their base
    3. **Student Engagement:** Multiple issues matter to student voters
    4. **Compromise Candidates:** Winners often balance multiple student concerns
    
    **Real-World Relevance:** Mirrors actual student government elections where
    candidates must appeal to diverse student body interests and priorities.
    """
    
    return ballot_data, description, analysis


def _create_city_council_scenario() -> tuple[BallotData, str, str]:
    """Create a municipal city council race."""
    ballots = []
    
    # Downtown/Business District voters (25%) - development, business-friendly
    for _ in range(45):
        ballots.append(["James Wilson", "Maria Rodriguez", "Patricia Chen", "Robert Taylor"])
    for _ in range(30):
        ballots.append(["James Wilson", "Patricia Chen", "Maria Rodriguez", "Robert Taylor"])
    
    # Eastside Neighborhood voters (30%) - affordable housing, community services
    for _ in range(55):
        ballots.append(["Maria Rodriguez", "Patricia Chen", "Robert Taylor", "James Wilson"])
    for _ in range(35):
        ballots.append(["Maria Rodriguez", "Robert Taylor", "Patricia Chen", "James Wilson"])
    
    # Westside/Suburban voters (25%) - schools, family services, traffic
    for _ in range(40):
        ballots.append(["Patricia Chen", "James Wilson", "Maria Rodriguez", "Robert Taylor"])
    for _ in range(35):
        ballots.append(["Patricia Chen", "Robert Taylor", "James Wilson", "Maria Rodriguez"])
    
    # Southside/Industrial voters (20%) - jobs, infrastructure, utilities
    for _ in range(35):
        ballots.append(["Robert Taylor", "Maria Rodriguez", "James Wilson", "Patricia Chen"])
    for _ in range(25):
        ballots.append(["Robert Taylor", "James Wilson", "Maria Rodriguez", "Patricia Chen"])
    
    ballot_data = BallotData(
        ballots=ballots,
        candidates={"James Wilson", "Maria Rodriguez", "Patricia Chen", "Robert Taylor"},
        total_ballots=len(ballots)
    )
    
    description = """
    **City Council Race**
    
    A municipal election representing different neighborhoods and their priorities.
    Demonstrates how RCV works with geographic and demographic voting patterns.
    
    **Candidates & Geographic Appeal:**
    - **James Wilson:** Business District focus - development, economic growth
    - **Maria Rodriguez:** Eastside advocate - affordable housing, social services
    - **Patricia Chen:** Westside focus - schools, families, suburban concerns  
    - **Robert Taylor:** Southside focus - jobs, infrastructure, industrial policy
    
    **Neighborhood Voting Patterns:**
    - Downtown/Business (25%): Pro-development priorities
    - Eastside (30%): Social justice and affordability focus
    - Westside/Suburban (25%): Family and education priorities
    - Southside/Industrial (20%): Jobs and infrastructure focus
    """
    
    analysis = """
    **Key Learning Points:**
    
    1. **Geographic Coalitions:** Neighborhoods have different but overlapping interests
    2. **Cross-District Appeal:** Candidates must reach beyond their home base
    3. **Municipal Governance:** City issues require balancing diverse community needs
    4. **Representative Democracy:** Winner represents entire city, not just largest bloc
    
    **Realistic Dynamics:** Based on actual municipal election patterns where
    candidates often have geographic strongholds but need citywide appeal to win.
    """
    
    return ballot_data, description, analysis