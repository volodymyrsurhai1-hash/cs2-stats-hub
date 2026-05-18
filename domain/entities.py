"""Domain entities - pure business objects without dependencies."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Player:
    """Represents a player in a match."""
    nickname: str
    player_id: str
    kills: int
    deaths: int
    adr: float
    kd_ratio: float
    headshots_pct: float


@dataclass(frozen=True)
class Team:
    """Represents a team in a match."""
    name: str
    score: int
    players: list[Player]


@dataclass(frozen=True)
class MatchRecord:
    """Represents a single match result."""
    match_id: str
    map_name: str
    win: bool
    kd_ratio: float
    kills: int
    deaths: int
    headshots: int
    played_at: datetime


@dataclass(frozen=True)
class PlayerStats:
    """Aggregated statistics for a player over multiple matches."""
    player_name: str
    total_matches: int
    kd_ratio: float
    headshot_pct: float
    winrate_pct: float
    average_kills: float
