"""Repository layer - data access and mapping from API to domain models."""
from typing import Optional
from datetime import datetime, timezone, timedelta

from infrastructure import FaceitAPIClient, FaceitAPIError
from domain import Player, Team, MatchRecord


class PlayerRepository:
    """Repository for fetching player data from Faceit API."""

    OFFSET_LIMIT = 200
    PAGE_SIZE = 100

    def __init__(self, api_client: FaceitAPIClient) -> None:
        self._api_client = api_client
        self._player_cache: dict[str, tuple[str, str]] = {}  # nickname -> (player_id, canonical_nickname)

    def get_player_id(self, nickname: str) -> tuple[str, str]:
        """Get player ID and canonical nickname. Returns (player_id, canonical_nickname)."""
        if nickname in self._player_cache:
            return self._player_cache[nickname]

        try:
            # Try exact search first
            data = self._api_client.get("players", params={"nickname": nickname})
            player_id = data["player_id"]
            canonical_nickname = data["nickname"]
        except FaceitAPIError as err:
            if err.status_code != 404:
                raise
            # Fallback to global search
            search_data = self._api_client.get(
                "search/players",
                params={"nickname": nickname, "game": "cs2", "limit": 1}
            )
            items = search_data.get("items", [])
            if not items:
                raise ValueError(f"Player '{nickname}' not found on Faceit.") from err

            first_match = items[0]
            player_id = first_match["player_id"]
            canonical_nickname = first_match["nickname"]

        self._player_cache[nickname] = (player_id, canonical_nickname)
        return player_id, canonical_nickname

    def get_player_info(self, nickname: str) -> dict:
        """Get full player information."""
        player_id, _ = self.get_player_id(nickname)
        return self._api_client.get(f"players/{player_id}")

    def fetch_match_stats(
        self,
        nickname: str,
        game: str = "cs2",
        period_days: Optional[int] = None
    ) -> list[dict]:
        """Fetch all match statistics for a player, bypassing API pagination limits.

        Uses offset-based pagination until OFFSET_LIMIT, then switches to
        timestamp-based pagination for older matches.
        """
        player_id, _ = self.get_player_id(nickname)
        history: list[dict] = []

        cutoff_dt = None
        if period_days:
            cutoff_dt = datetime.now(timezone.utc) - timedelta(days=period_days)

        while True:
            # Choose pagination strategy
            if len(history) <= self.OFFSET_LIMIT:
                params = {"limit": self.PAGE_SIZE, "offset": len(history)}
            else:
                last_ts = history[-1].get("Match Finished At")
                params = {"limit": self.PAGE_SIZE, "to": last_ts}

            data = self._api_client.get(
                f"players/{player_id}/games/{game}/stats",
                params=params
            )
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                stats = item.get("stats", {})

                # Check if match is within requested period
                if cutoff_dt:
                    ts_str = stats.get("Updated At", "")
                    if ts_str:
                        try:
                            match_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if match_dt < cutoff_dt:
                                return history
                        except (ValueError, TypeError, AttributeError):
                            pass

                history.append(stats)

            if len(items) < self.PAGE_SIZE:
                break

        return history

    def get_match_details(self, match_id: str) -> list[Team]:
        """Get detailed match information including all players and teams."""
        data = self._api_client.get(f"matches/{match_id}/stats")
        teams: list[Team] = []

        for round_data in data.get("rounds", []):
            for team_data in round_data.get("teams", []):
                players: list[Player] = []

                for player_data in team_data.get("players", []):
                    stats = player_data.get("player_stats", {})

                    # Parse headshots percentage (remove % sign)
                    hs_pct_str = stats.get("Headshots %", "0")
                    hs_pct = float(hs_pct_str.rstrip("%"))

                    player = Player(
                        nickname=player_data.get("nickname", ""),
                        player_id=player_data.get("player_id", ""),
                        kills=int(stats.get("Kills", 0)),
                        deaths=int(stats.get("Deaths", 0)),
                        adr=float(stats.get("ADR", 0)),
                        kd_ratio=float(stats.get("K/D Ratio", 0)),
                        headshots_pct=hs_pct,
                    )
                    players.append(player)

                team_stats = team_data.get("team_stats", {})
                team = Team(
                    name=team_stats.get("Team", "Unknown"),
                    score=int(team_stats.get("Final Score", 0)),
                    players=players
                )
                teams.append(team)

        return teams
