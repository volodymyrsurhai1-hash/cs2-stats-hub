"""Presentation layer - formatting data for display."""
from datetime import datetime
from domain import PlayerStats, MatchRecord, Team, Player


class StatsFormatter:
    """Formats domain objects for UI display."""

    @staticmethod
    def format_player_stats(stats: PlayerStats) -> dict[str, str]:
        """Format PlayerStats for display."""
        return {
            "Name": stats.player_name,
            "Matches": str(stats.total_matches),
            "KD": f"{stats.kd_ratio:.2f}",
            "Headshots": f"{stats.headshot_pct:.0f}%",
            "Winrate": f"{stats.winrate_pct:.1f}%",
            "Average Kills": f"{stats.average_kills:.1f}",
        }

    @staticmethod
    def format_match_record(match: MatchRecord) -> dict[str, str]:
        """Format MatchRecord for display."""
        return {
            "Map": match.map_name,
            "Result": "Win" if match.win else "Loss",
            "KD": f"{match.kd_ratio:.2f}",
            "Kills": str(match.kills),
            "Deaths": str(match.deaths),
            "Headshots": str(match.headshots),
            "Date": match.played_at.strftime("%d %b %Y"),
        }

    @staticmethod
    def format_player(player: Player) -> dict[str, str]:
        """Format Player for display."""
        return {
            "Nickname": player.nickname,
            "Kills": str(player.kills),
            "Deaths": str(player.deaths),
            "KD": f"{player.kd_ratio:.2f}",
            "ADR": f"{player.adr:.1f}",
            "HS%": f"{player.headshots_pct:.0f}%",
        }

    @staticmethod
    def format_team(team: Team) -> dict[str, any]:
        """Format Team for display."""
        return {
            "name": team.name,
            "score": team.score,
            "players": [StatsFormatter.format_player(p) for p in team.players],
        }

    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format datetime to readable string."""
        return dt.strftime("%d %b %Y %H:%M")
