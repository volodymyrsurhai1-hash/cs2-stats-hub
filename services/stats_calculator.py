"""Business logic for calculating statistics."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchStatsSum:
    """Aggregated raw statistics from multiple matches."""
    total_matches: int
    total_kills: int
    total_deaths: int
    total_headshots: int
    wins: int


class StatsCalculator:
    """Calculator for aggregating and computing player statistics."""

    @staticmethod
    def sum_match_stats(match_stats: list[dict]) -> MatchStatsSum:
        """Sum raw statistics from multiple matches."""
        total_matches = len(match_stats)
        total_kills = 0
        total_deaths = 0
        total_headshots = 0
        wins = 0

        for stats in match_stats:
            total_kills += int(stats.get("Kills", 0))
            total_deaths += int(stats.get("Deaths", 0))
            total_headshots += int(stats.get("Headshots", 0))
            if stats.get("Result") == "1":
                wins += 1

        return MatchStatsSum(
            total_matches=total_matches,
            total_kills=total_kills,
            total_deaths=total_deaths,
            total_headshots=total_headshots,
            wins=wins
        )

    @staticmethod
    def calculate_kd_ratio(kills: int, deaths: int) -> float:
        """Calculate K/D ratio."""
        return kills / deaths if deaths > 0 else float(kills)

    @staticmethod
    def calculate_headshot_percentage(headshots: int, kills: int) -> float:
        """Calculate headshot percentage."""
        return (headshots / kills * 100) if kills > 0 else 0.0

    @staticmethod
    def calculate_winrate(wins: int, total_matches: int) -> float:
        """Calculate winrate percentage."""
        return (wins / total_matches * 100) if total_matches > 0 else 0.0

    @staticmethod
    def calculate_average_kills(kills: int, matches: int) -> float:
        """Calculate average kills per match."""
        return kills / matches if matches > 0 else 0.0
