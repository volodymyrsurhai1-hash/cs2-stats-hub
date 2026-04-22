import requests
from config import API_FACEIT
import json
from typing import Any, Protocol, Optional, Union
from dataclasses import dataclass


HEADERS = {
    "Authorization": f"Bearer {API_FACEIT}",
    "Accept": "application/json"
}


@dataclass
class PlayerStats:
    matches: int
    kd_ratio: float
    headshot_pct: float   # 0.0–100.0
    winrate_pct: float    # 0.0–100.0
    average_kills: float
    def as_display(self) -> dict[str, str]:
        """Строковое представление для UI."""
        return {
            "Matches": str(self.matches),
            "KD": f"{self.kd_ratio:.2f}",
            "Headshots": f"{self.headshot_pct:.0f}%",
            "Winrate": f"{self.winrate_pct:.1f}%",
            "Average Kills": f"{self.average_kills:.0f}",
        }

@dataclass
class MatchRecord:
    map: str
    win: bool
    kd: str
    kills: int
    deaths: int
    headshots: int
    played_at: str   

# class Player(Protocol):
#     nickname: str
#     def get_player(self) -> Union[dict[str, Any], str]: ...
#     def get_player_stats(self) -> Union[dict[str, Any], str]: ...
#     def get_player_matches(self) -> Union[dict[str, Any], str]: ...




class FaceitAPIError(Exception):
    """Любая ошибка при обращении к Faceit API."""
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class FaceitPlayer:
    def __init__(self, nickname: str) -> None:
        self.nickname = nickname
        self._cached_player_id: Optional[str] = None

    @staticmethod
    def _get_json_response(endpoint: str, params: dict = None) -> dict[str, Any]:
        # URL формируется здесь
        url = f"https://open.faceit.com/data/v4/{endpoint}"
        response = requests.get(url,
                                headers=HEADERS,
                                params=params)

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            raise FaceitAPIError(
                status_code=err.response.status_code,
                message=str(err)
            ) from err

    @property
    def _player_id(self) -> str:
        """Получает ID: сначала точный поиск, если 404 — глобальный"""
        if self._cached_player_id is None:
            try:
                # 1. Точный поиск по никнейму
                data = self._get_json_response("players", params={"nickname": self.nickname})
                self._cached_player_id = data.get("player_id", "")
            except FaceitAPIError as err:
                if err.status_code != 404:
                    raise
                # 2. Fallback — глобальный поиск (только при 404)
                search_data = self._get_json_response(
                    "search/players",
                    params={"nickname": self.nickname, "game": "cs2", "limit": 1}
                )
                items = search_data.get("items", [])
                if not items:
                    raise ValueError(f"Игрок '{self.nickname}' не найден на Faceit.") from err
                first_match = items[0]
                self._cached_player_id = first_match.get("player_id", "")
                self.nickname = first_match.get("nickname", self.nickname)

        return self._cached_player_id

    def get_player(self) -> Union[dict[str, Any], str]:
        return self._get_json_response(f"players/{self._player_id}")

    def get_player_stats(self) -> dict[str, int | str]:
        data = self._get_json_response(f"players/{self._player_id}/games/cs2/stats", params={
            "limit": 100
        })


        items = data.get("items", [])
        total_matches = len(items)
        total_kills = 0
        total_deaths = 0
        total_headshots = 0
        wins = 0

        for item in items:
            stats = item.get("stats", {})
            total_kills += int(stats.get("Kills", 0))
            total_deaths += int(stats.get("Deaths", 0))
            total_headshots += int(stats.get("Headshots", 0))
            if stats.get("Result") == "1":
                wins += 1


        return PlayerStats(
        matches=total_matches,
        kd_ratio=total_kills / total_deaths if total_deaths > 0 else float(total_kills),
        headshot_pct=(total_headshots / total_kills * 100) if total_kills > 0 else 0.0,
        winrate_pct=(wins / total_matches * 100) if total_matches > 0 else 0.0,
        average_kills=total_kills / total_matches if total_matches > 0 else 0,
    )


    def get_player_matches(self) -> Union[dict[str, Any], str]:
        data = self._get_json_response(f"players/{self._player_id}/games/cs2/stats", params={
            "limit": 100
        })
        result = []
        for item in data.get("items", []):
            s = item.get("stats", {})
            result.append(MatchRecord(
                map=s.get("Map", ""),
                win=s.get("Result") == "1",
                kd=s.get("K/D Ratio", "0"),
                kills=int(s.get("Kills", 0)),
                deaths=int(s.get("Deaths", 0)),
                headshots=int(s.get("Headshots", 0)),
                played_at=s.get("Updated At", ""),
            ))
        return result


    def __repr__(self) -> str:
        return f"<FaceitPlayer {self.nickname}>"



if __name__ == "__main__":
    player = FaceitPlayer("matb_shluyxa")
    matches = player.get_player_matches()
    stats = player.get_player_stats()
    print(matches, "\n", stats.as_display())




