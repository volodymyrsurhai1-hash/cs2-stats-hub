"""Service layer - orchestrates business logic and data access."""
from typing import Optional
from datetime import datetime

from domain import PlayerStats, MatchRecord, Team
from repository import PlayerRepository
from services.stats_calculator import StatsCalculator


class PlayerService:
    """High-level service for player-related operations."""

    def __init__(self, repository: PlayerRepository, calculator: StatsCalculator) -> None:
        self._repository = repository
        self._calculator = calculator

    def get_player_stats(self, nickname: str, period_days: Optional[int] = None) -> PlayerStats:
        """Get aggregated statistics for a player."""
        # Fetch raw match data
        match_stats = self._repository.fetch_match_stats(nickname, period_days=period_days)

        # Get canonical nickname
        _, canonical_nickname = self._repository.get_player_id(nickname)

        # Calculate aggregated stats
        summed = self._calculator.sum_match_stats(match_stats)

        return PlayerStats(
            player_name=canonical_nickname,
            total_matches=summed.total_matches,
            kd_ratio=self._calculator.calculate_kd_ratio(summed.total_kills, summed.total_deaths),
            headshot_pct=self._calculator.calculate_headshot_percentage(
                summed.total_headshots, summed.total_kills
            ),
            winrate_pct=self._calculator.calculate_winrate(summed.wins, summed.total_matches),
            average_kills=self._calculator.calculate_average_kills(
                summed.total_kills, summed.total_matches
            ),
        )

    def get_player_matches(self, nickname: str, period_days: Optional[int] = None) -> list[MatchRecord]:
        """Get list of matches for a player."""
        match_stats = self._repository.fetch_match_stats(nickname, period_days=period_days)

        matches: list[MatchRecord] = []
        for stats in match_stats:
            try:
                # Parse timestamp
                ts_str = stats.get("Updated At", "")
                played_at = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError, AttributeError):
                played_at = datetime.now()

            match = MatchRecord(
                match_id=stats.get("Match Id", ""),
                map_name=stats.get("Map", "Unknown"),
                win=stats.get("Result") == "1",
                kd_ratio=float(stats.get("K/D Ratio", 0)),
                kills=int(stats.get("Kills", 0)),
                deaths=int(stats.get("Deaths", 0)),
                headshots=int(stats.get("Headshots", 0)),
                played_at=played_at,
            )
            matches.append(match)

        return matches

    def get_match_details(self, match_id: str) -> list[Team]:
        """Get detailed information about a specific match."""
        return self._repository.get_match_details(match_id)
