import pytest
from services.stats_calculator import StatsCalculator, MatchStatsSum

def test_sum_match_stats():
    match_stats = [
        {"Kills": "10", "Deaths": "5", "Headshots": "5", "Result": "1"},
        {"Kills": "5", "Deaths": "10", "Headshots": "2", "Result": "0"},
        # Missing keys test
        {"Result": "1"}
    ]
    result = StatsCalculator.sum_match_stats(match_stats)
    
    assert result.total_matches == 3
    assert result.total_kills == 15
    assert result.total_deaths == 15
    assert result.total_headshots == 7
    assert result.wins == 2

def test_calculate_kd_ratio():
    assert StatsCalculator.calculate_kd_ratio(10, 5) == 2.0
    assert StatsCalculator.calculate_kd_ratio(10, 0) == 10.0
    assert StatsCalculator.calculate_kd_ratio(0, 5) == 0.0

def test_calculate_headshot_percentage():
    assert StatsCalculator.calculate_headshot_percentage(5, 10) == 50.0
    assert StatsCalculator.calculate_headshot_percentage(0, 10) == 0.0
    assert StatsCalculator.calculate_headshot_percentage(5, 0) == 0.0

def test_calculate_winrate():
    assert StatsCalculator.calculate_winrate(1, 2) == 50.0
    assert StatsCalculator.calculate_winrate(3, 3) == 100.0
    assert StatsCalculator.calculate_winrate(0, 5) == 0.0
    assert StatsCalculator.calculate_winrate(5, 0) == 0.0

def test_calculate_average_kills():
    assert StatsCalculator.calculate_average_kills(20, 2) == 10.0
    assert StatsCalculator.calculate_average_kills(0, 2) == 0.0
    assert StatsCalculator.calculate_average_kills(10, 0) == 0.0
