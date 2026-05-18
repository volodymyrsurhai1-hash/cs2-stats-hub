"""Facade for backward compatibility - wraps new clean architecture.

This file maintains the old API while using the new layered architecture internally.
For new code, use the services/domain layers directly.
"""
from typing import Optional
from config import API_FACEIT

from infrastructure import FaceitAPIClient
from repository import PlayerRepository
from services import PlayerService, StatsCalculator
from presentation import StatsFormatter
from domain import PlayerStats, MatchRecord, Team

# Re-export domain entities for backward compatibility
__all__ = ["FaceitPlayer", "PlayerStats", "MatchRecord", "Team"]


class FaceitPlayer:
    """Facade class that wraps the new architecture with old API.

    DEPRECATED: For new code, use PlayerService directly.
    This class exists only for backward compatibility.
    """

    def __init__(self, nickname: str) -> None:
        self.nickname = nickname

        # Initialize layers
        api_client = FaceitAPIClient(API_FACEIT)
        repository = PlayerRepository(api_client)
        calculator = StatsCalculator()
        self._service = PlayerService(repository, calculator)
        self._formatter = StatsFormatter()

    def get_player_stats(self, period_days: Optional[int] = None) -> PlayerStats:
        """Get aggregated player statistics."""
        return self._service.get_player_stats(self.nickname, period_days)

    def get_player_matches(self, period_days: Optional[int] = None) -> list[MatchRecord]:
        """Get player match history."""
        return self._service.get_player_matches(self.nickname, period_days)

    def get_room_of_match(self, match_id: str) -> list[Team]:
        """Get detailed match information."""
        return self._service.get_match_details(match_id)

    def __repr__(self) -> str:
        return f"<FaceitPlayer {self.nickname}>"


if __name__ == "__main__":
    # Example usage
    player = FaceitPlayer("matb_shluyxa")
    stats = player.get_player_stats(30)
    print(f"Stats: {stats}")

    matches = player.get_player_matches(30)
    if matches:
        match_details = player.get_room_of_match(matches[0].match_id)
        print(f"First match details: {match_details}")
