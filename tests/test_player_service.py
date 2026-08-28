import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from services.player_service import PlayerService
from services.stats_calculator import StatsCalculator, MatchStatsSum
from domain.entities import PlayerStats, MatchRecord, Team


@pytest.fixture
def mock_repository():
    repo = Mock()
    # default side effects or return values for repository
    repo.get_player_id.return_value = ("id_123", "CanonicalName")
    return repo


@pytest.fixture
def mock_calculator():
    return Mock(spec=StatsCalculator)


@pytest.fixture
def player_service(mock_repository, mock_calculator):
    return PlayerService(repository=mock_repository, calculator=mock_calculator)


def test_get_player_stats(player_service, mock_repository, mock_calculator):
    # Arrange
    mock_repository.fetch_match_stats.return_value = [{"Kills": "10", "Deaths": "5"}]
    mock_calculator.sum_match_stats.return_value = MatchStatsSum(
        total_matches=1, total_kills=10, total_deaths=5, total_headshots=5, wins=1
    )
    mock_calculator.calculate_kd_ratio.return_value = 2.0
    mock_calculator.calculate_headshot_percentage.return_value = 50.0
    mock_calculator.calculate_winrate.return_value = 100.0
    mock_calculator.calculate_average_kills.return_value = 10.0

    # Act
    stats = player_service.get_player_stats("test_nick", period_days=30)

    # Assert
    mock_repository.fetch_match_stats.assert_called_once_with("test_nick", period_days=30)
    mock_repository.get_player_id.assert_called_once_with("test_nick")
    
    assert isinstance(stats, PlayerStats)
    assert stats.player_name == "CanonicalName"
    assert stats.total_matches == 1
    assert stats.kd_ratio == 2.0


def test_get_player_matches(player_service, mock_repository):
    # Arrange
    mock_repository.fetch_match_stats.return_value = [
        {
            "Match Id": "match_1",
            "Map": "de_mirage",
            "Result": "1",
            "K/D Ratio": "1.5",
            "Kills": "15",
            "Deaths": "10",
            "Headshots": "5",
            "Updated At": "2023-01-01T12:00:00Z"
        },
        {
            "Match Id": "match_2" # Testing fallback defaults
        }
    ]

    # Act
    matches = player_service.get_player_matches("test_nick", period_days=None)

    # Assert
    assert len(matches) == 2
    
    assert matches[0].match_id == "match_1"
    assert matches[0].map_name == "de_mirage"
    assert matches[0].win is True
    assert matches[0].kd_ratio == 1.5
    assert matches[0].kills == 15
    assert matches[0].played_at == datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    
    assert matches[1].match_id == "match_2"
    assert matches[1].map_name == "Unknown"
    assert matches[1].win is False
    assert matches[1].kills == 0
    # timestamp should be roughly now or a valid datetime type
    assert isinstance(matches[1].played_at, datetime)


def test_get_match_details(player_service, mock_repository):
    # Arrange
    expected_teams = [Mock(spec=Team), Mock(spec=Team)]
    mock_repository.get_match_details.return_value = expected_teams
    
    # Act
    teams = player_service.get_match_details("match_123")
    
    # Assert
    mock_repository.get_match_details.assert_called_once_with("match_123")
    assert teams == expected_teams
