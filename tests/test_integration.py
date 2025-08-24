"""Integration tests for the RCV Dashboard end-to-end workflows.

This module tests complete workflows from ballot loading through RCV processing
to results export, ensuring all components work together correctly.
"""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from src.rcv_dashboard.core.ballot_loader import load_ballots_from_uploaded_file
from src.rcv_dashboard.core.rcv_processor import RCVProcessor  
from src.rcv_dashboard.simulation.scenarios import load_scenario
from src.rcv_dashboard.utils.file_utils import (
    create_ballot_template_csv,
    create_ballot_template_excel,
    export_results_to_csv,
    create_comprehensive_export_zip,
)
from src.rcv_dashboard.visualization.charts import (
    create_vote_progression_chart,
    create_vote_transfer_sankey,
)
from src.rcv_dashboard.visualization.tables import (
    create_round_results_table,
    create_candidate_summary_table,
)


class MockUploadedFile:
    """Mock uploaded file for testing."""
    
    def __init__(self, content: bytes, name: str):
        self.content = content
        self.name = name
        self.size = len(content)
    
    def read(self) -> bytes:
        return self.content
    
    def getvalue(self) -> bytes:
        return self.content


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_csv_upload_to_results_workflow(self) -> None:
        """Test complete workflow from CSV upload to election results."""
        # Step 1: Create CSV ballot data
        csv_content = """Choice 1,Choice 2,Choice 3
Alice Johnson,Bob Smith,Charlie Brown
Alice Johnson,Charlie Brown,Bob Smith
Bob Smith,Alice Johnson,Charlie Brown
Bob Smith,Charlie Brown,Alice Johnson
Charlie Brown,Alice Johnson,Bob Smith
Alice Johnson,Bob Smith,Charlie Brown
Alice Johnson,Charlie Brown,Bob Smith
Bob Smith,Alice Johnson,Charlie Brown"""
        
        mock_file = MockUploadedFile(csv_content.encode(), "test_ballots.csv")
        
        # Step 2: Load ballots from uploaded file
        ballot_data = load_ballots_from_uploaded_file(mock_file)
        
        assert ballot_data is not None
        assert ballot_data.total_ballots == 8
        assert len(ballot_data.candidates) == 3
        assert "Alice Johnson" in ballot_data.candidates
        assert "Bob Smith" in ballot_data.candidates
        assert "Charlie Brown" in ballot_data.candidates
        
        # Step 3: Process RCV election
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        assert election_result.winner is not None
        assert election_result.total_ballots == 8
        assert len(election_result.candidates) == 3
        assert len(election_result.rounds) >= 1
        
        # Step 4: Generate visualizations
        vote_chart = create_vote_progression_chart(election_result)
        sankey_chart = create_vote_transfer_sankey(election_result)
        
        assert vote_chart is not None
        assert sankey_chart is not None
        
        # Step 5: Generate tables
        round_table = create_round_results_table(election_result)
        candidate_table = create_candidate_summary_table(election_result)
        
        assert round_table is not None
        assert candidate_table is not None
        assert len(round_table) >= len(election_result.rounds)
        assert len(candidate_table) == len(election_result.candidates)
        
        # Step 6: Export results
        csv_export = export_results_to_csv(election_result)
        assert isinstance(csv_export, bytes)
        assert len(csv_export) > 0
        
        # Verify CSV export contains key information
        csv_str = csv_export.decode('utf-8')
        assert election_result.winner in csv_str
        assert "ELECTION SUMMARY" in csv_str
        assert "ROUND RESULTS" in csv_str
    
    def test_excel_upload_to_export_workflow(self) -> None:
        """Test complete workflow from Excel upload to ZIP export."""
        # Step 1: Create Excel ballot data
        df = pd.DataFrame({
            'Choice 1': ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob'],
            'Choice 2': ['Bob', 'Alice', 'Alice', 'Charlie', 'Charlie'], 
            'Choice 3': ['Charlie', 'Charlie', 'Bob', 'Bob', 'Alice']
        })
        
        # Save to bytes
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False, engine='openpyxl')
            excel_content = buffer.getvalue()
        
        mock_file = MockUploadedFile(excel_content, "test_ballots.xlsx")
        
        # Step 2: Load and process
        ballot_data = load_ballots_from_uploaded_file(mock_file)
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Step 3: Create comprehensive export
        charts_data = {
            "vote_progression.png": b"mock_chart_data",
            "vote_transfers.html": b"<html>mock sankey chart</html>"
        }
        
        zip_export = create_comprehensive_export_zip(election_result, charts_data)
        
        # Step 4: Verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_export), 'r') as zip_file:
            file_names = zip_file.namelist()
            
            # Should contain results and charts
            assert any("results.csv" in name for name in file_names)
            assert any("summary.txt" in name for name in file_names)
            assert any("vote_progression.png" in name for name in file_names)
            assert any("vote_transfers.html" in name for name in file_names)
            
            # Verify file contents
            for file_name in file_names:
                file_content = zip_file.read(file_name)
                assert len(file_content) > 0
    
    def test_scenario_to_visualization_workflow(self) -> None:
        """Test workflow from demo scenario to visualizations."""
        # Step 1: Load demo scenario
        ballot_data, description, analysis = load_scenario("Classic Spoiler Effect")
        
        assert ballot_data.total_ballots > 0
        assert len(description) > 0
        assert len(analysis) > 0
        
        # Step 2: Process election
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Step 3: Generate all visualization types
        vote_chart = create_vote_progression_chart(election_result)
        sankey_chart = create_vote_transfer_sankey(election_result)
        
        assert vote_chart is not None
        assert sankey_chart is not None
        
        # Step 4: Verify visualization data makes sense
        # Chart should have data for all rounds
        assert hasattr(vote_chart, 'data') or hasattr(vote_chart, 'to_json')
        
        # Sankey should show vote transfers if multi-round election
        if len(election_result.rounds) > 1:
            assert sankey_chart is not None
    
    def test_template_generation_to_upload_workflow(self) -> None:
        """Test workflow from template generation back to upload."""
        candidates = ["Alice Johnson", "Bob Smith", "Charlie Brown", "David Wilson"]
        
        # Step 1: Generate CSV template
        csv_template = create_ballot_template_csv(candidates, num_sample_ballots=10)
        
        # Step 2: Use template as if it were uploaded
        mock_file = MockUploadedFile(csv_template, "generated_template.csv")
        ballot_data = load_ballots_from_uploaded_file(mock_file)
        
        # Step 3: Verify template produces valid election
        assert ballot_data.total_ballots == 10  # Sample ballots
        assert len(ballot_data.candidates) == 4
        assert set(ballot_data.candidates) == set(candidates)
        
        # Step 4: Process the template data
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        assert election_result.winner in candidates
        assert election_result.total_ballots == 10
    
    def test_large_election_workflow(self) -> None:
        """Test workflow with a larger, more complex election."""
        # Generate a larger election scenario
        candidates = [f"Candidate {i}" for i in range(1, 8)]  # 7 candidates
        
        # Create realistic ballot distribution
        ballots = []
        import random
        random.seed(42)  # For reproducible tests
        
        for _ in range(500):  # 500 voters
            # Each voter ranks 2-6 candidates randomly
            num_choices = random.randint(2, 6)
            ballot = random.sample(candidates, num_choices)
            ballots.append(ballot)
        
        # Create ballot data
        from src.rcv_dashboard.core.models import BallotData
        ballot_data = BallotData(
            ballots=ballots,
            candidates=candidates,
            total_ballots=500,
            candidate_count=7
        )
        
        # Process large election
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Verify results make sense for large election
        assert election_result.winner is not None
        assert election_result.total_ballots == 500
        assert len(election_result.candidates) == 7
        
        # Should require multiple rounds for 7 candidates
        assert len(election_result.rounds) >= 2
        
        # Generate visualizations for large election
        vote_chart = create_vote_progression_chart(election_result)
        sankey_chart = create_vote_transfer_sankey(election_result)
        
        assert vote_chart is not None
        assert sankey_chart is not None
        
        # Export large election results
        csv_export = export_results_to_csv(election_result)
        assert len(csv_export) > 1000  # Should be substantial for large election
    
    def test_error_recovery_workflow(self) -> None:
        """Test workflow error handling and recovery."""
        # Test with invalid CSV data
        invalid_csv = "Not,Valid,CSV,Data\n1,2,3,4,5,6,7,8,9,10"  # Too many columns
        mock_file = MockUploadedFile(invalid_csv.encode(), "invalid.csv")
        
        # Should handle invalid data gracefully
        try:
            ballot_data = load_ballots_from_uploaded_file(mock_file)
            if ballot_data is not None:
                # If it loads, it should still be processable
                processor = RCVProcessor(ballot_data)
                election_result = processor.run_election()
                assert election_result is not None
        except Exception as e:
            # Should raise a meaningful error
            assert isinstance(e, (ValueError, RuntimeError))
            assert len(str(e)) > 0


class TestScenarioIntegration:
    """Test integration of all demo scenarios."""
    
    def test_all_scenarios_complete_workflow(self) -> None:
        """Test that all demo scenarios can complete the full workflow."""
        from src.rcv_dashboard.simulation.scenarios import get_scenario_list
        
        scenarios = get_scenario_list()
        
        for scenario_name in scenarios:
            # Load scenario
            ballot_data, description, analysis = load_scenario(scenario_name)
            
            # Process election
            processor = RCVProcessor(ballot_data)
            election_result = processor.run_election()
            
            # Verify basic election properties
            assert election_result.winner is not None, f"No winner in {scenario_name}"
            assert election_result.total_ballots > 0, f"No ballots in {scenario_name}"
            assert len(election_result.rounds) >= 1, f"No rounds in {scenario_name}"
            
            # Generate key visualizations
            vote_chart = create_vote_progression_chart(election_result)
            candidate_table = create_candidate_summary_table(election_result)
            
            assert vote_chart is not None, f"Chart failed for {scenario_name}"
            assert candidate_table is not None, f"Table failed for {scenario_name}"
            assert len(candidate_table) > 0, f"Empty table for {scenario_name}"
            
            # Export results
            csv_export = export_results_to_csv(election_result)
            assert len(csv_export) > 100, f"Export too small for {scenario_name}"


class TestDataConsistency:
    """Test data consistency across the entire pipeline."""
    
    def test_vote_count_consistency(self) -> None:
        """Test that vote counts remain consistent throughout processing."""
        # Load a scenario with known vote counts
        ballot_data, _, _ = load_scenario("Landslide Victory")
        
        # Track total ballots through pipeline
        original_ballots = ballot_data.total_ballots
        
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Verify ballot counts are preserved
        assert election_result.total_ballots == original_ballots
        
        # Verify vote counts in each round sum correctly
        for round_result in election_result.rounds:
            total_round_votes = sum(round_result.vote_counts.values())
            # Should be <= original ballots (some ballots may be exhausted)
            assert total_round_votes <= original_ballots
            assert total_round_votes > 0
            
        # Verify candidate totals are consistent
        for candidate in election_result.candidates:
            # First choice votes should be non-negative
            assert candidate.first_choice_votes >= 0
            
            # Final votes should be non-negative
            assert candidate.final_votes >= 0
            
            # Winner should have more final votes than first choice votes
            # (unless they won in first round)
            if candidate.is_winner and len(election_result.rounds) > 1:
                assert candidate.final_votes >= candidate.first_choice_votes
    
    def test_candidate_consistency(self) -> None:
        """Test that candidate information remains consistent."""
        ballot_data, _, _ = load_scenario("Close Three-Way Race")
        
        # Get original candidates
        original_candidates = set(ballot_data.candidates)
        
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Verify all original candidates appear in results
        result_candidates = {c.name for c in election_result.candidates}
        assert result_candidates == original_candidates
        
        # Verify exactly one winner
        winners = [c for c in election_result.candidates if c.is_winner]
        assert len(winners) == 1
        
        # Verify winner is consistent across data structures
        winner_name = winners[0].name
        assert election_result.winner == winner_name
        
        # Winner should appear as winner in final round
        final_round = election_result.rounds[-1]
        assert final_round.winner == winner_name
    
    def test_round_progression_consistency(self) -> None:
        """Test that round progression follows RCV rules."""
        ballot_data, _, _ = load_scenario("Polarized vs Consensus")
        
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # Verify round numbering is sequential
        for i, round_result in enumerate(election_result.rounds):
            assert round_result.round_number == i + 1
        
        # Verify candidate elimination progression
        remaining_candidates = set(ballot_data.candidates)
        
        for round_result in election_result.rounds[:-1]:  # All but last round
            # Should have eliminated candidate (unless first round majority)
            if round_result.eliminated_candidate:
                assert round_result.eliminated_candidate in remaining_candidates
                remaining_candidates.remove(round_result.eliminated_candidate)
                
                # Eliminated candidate should not appear in subsequent rounds
                next_round = election_result.rounds[round_result.round_number]
                assert round_result.eliminated_candidate not in next_round.vote_counts
        
        # Final round should have a winner
        final_round = election_result.rounds[-1]
        assert final_round.winner is not None
        assert final_round.winner in remaining_candidates


class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows."""
    
    def test_large_election_performance(self) -> None:
        """Test performance with large elections (performance regression test)."""
        # Create a large election
        candidates = [f"Candidate {i:02d}" for i in range(1, 21)]  # 20 candidates
        
        # Generate 2000 ballots
        ballots = []
        import random
        random.seed(123)  # Reproducible
        
        for _ in range(2000):
            # Each voter ranks 5-15 candidates
            num_choices = random.randint(5, 15)
            ballot = random.sample(candidates, num_choices)
            ballots.append(ballot)
        
        from src.rcv_dashboard.core.models import BallotData
        ballot_data = BallotData(
            ballots=ballots,
            candidates=candidates,
            total_ballots=2000,
            candidate_count=20
        )
        
        # Time the processing (basic performance check)
        import time
        start_time = time.time()
        
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        processing_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 10 seconds)
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f}s"
        
        # Verify results are valid
        assert election_result.winner is not None
        assert election_result.total_ballots == 2000
        assert len(election_result.candidates) == 20
        
        # Generate visualizations (should also be reasonably fast)
        start_time = time.time()
        
        vote_chart = create_vote_progression_chart(election_result)
        sankey_chart = create_vote_transfer_sankey(election_result)
        
        viz_time = time.time() - start_time
        
        # Visualization should complete in reasonable time
        assert viz_time < 5.0, f"Visualization took too long: {viz_time:.2f}s"
        
        assert vote_chart is not None
        assert sankey_chart is not None


class TestUserExperienceIntegration:
    """Test workflows from a user experience perspective."""
    
    def test_typical_user_workflow(self) -> None:
        """Test the most common user workflow paths."""
        # Scenario 1: User uploads their own CSV file
        csv_content = """First Choice,Second Choice,Third Choice
Alice,Bob,Charlie
Bob,Alice,Charlie
Charlie,Alice,Bob
Alice,Charlie,Bob
Bob,Charlie,Alice"""
        
        mock_file = MockUploadedFile(csv_content.encode(), "my_election.csv")
        
        # User uploads file
        ballot_data = load_ballots_from_uploaded_file(mock_file)
        
        # System processes election
        processor = RCVProcessor(ballot_data)
        election_result = processor.run_election()
        
        # User views results and visualizations
        vote_chart = create_vote_progression_chart(election_result)
        round_table = create_round_results_table(election_result)
        
        # User exports results
        csv_export = export_results_to_csv(election_result)
        zip_export = create_comprehensive_export_zip(election_result, {
            "chart.png": b"mock_chart"
        })
        
        # Verify complete user experience
        assert election_result.winner is not None
        assert vote_chart is not None
        assert round_table is not None
        assert len(csv_export) > 0
        assert len(zip_export) > 0
    
    def test_educational_user_workflow(self) -> None:
        """Test workflow for educational users exploring RCV concepts."""
        # User explores demo scenarios
        scenarios = ["Classic Spoiler Effect", "Polarized vs Consensus"]
        
        results = []
        for scenario_name in scenarios:
            # User loads demo scenario
            ballot_data, description, analysis = load_scenario(scenario_name)
            
            # User processes the scenario
            processor = RCVProcessor(ballot_data)
            election_result = processor.run_election()
            
            # User examines the results
            vote_chart = create_vote_progression_chart(election_result)
            sankey_chart = create_vote_transfer_sankey(election_result)
            
            results.append({
                'scenario': scenario_name,
                'result': election_result,
                'description': description,
                'analysis': analysis,
                'vote_chart': vote_chart,
                'sankey_chart': sankey_chart
            })
        
        # Verify educational value
        for result in results:
            assert result['result'].winner is not None
            assert len(result['description']) > 50
            assert len(result['analysis']) > 50
            assert result['vote_chart'] is not None
            assert result['sankey_chart'] is not None
            
        # Different scenarios should produce different outcomes
        assert results[0]['result'].winner != results[1]['result'].winner or \
               len(results[0]['result'].rounds) != len(results[1]['result'].rounds)