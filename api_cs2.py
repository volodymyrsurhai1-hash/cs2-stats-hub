import requests
from config import API_FACEIT
import json
from typing import Any, Protocol, Optional, Union
import time

HEADERS = {
    "Authorization": f"Bearer {API_FACEIT}",
    "Accept": "application/json"
}


class Player(Protocol):
    nickname: str
    def get_player(self) -> Union[dict[str, Any], str]: ...
    def get_player_stats(self) -> Union[dict[str, Any], str]: ...
    def get_player_matches(self) -> Union[dict[str, Any], str]: ...



class FaceitPlayer:
    def __init__(self, nickname: str) -> None:
        self.nickname = nickname
        self._cached_player_id: Optional[str] = None

    @staticmethod
    def _get_json_response(endpoint: str, params: dict = None) -> Union[dict[str, Any], str]:
        # URL формируется здесь
        url = f"https://open.faceit.com/data/v4/{endpoint}"
        response = requests.get(url,
                                headers=HEADERS,
                                params=params)

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            return f"Ошибка запроса: {err}"

    @property
    def _player_id(self) -> str:
        """Получает ID: сначала точный поиск, если 404 — глобальный"""
        if self._cached_player_id is None:
            # 1. Точный поиск
            data = self._get_json_response("players", params={"nickname": self.nickname})

            if isinstance(data, str):
                search_data = self._get_json_response(
                    "search/players",
                    params={"nickname": self.nickname, "game": "cs2", "limit": 1}
                )

                if isinstance(search_data, dict) and search_data.get("items"):
                    first_match = search_data["items"][0]
                    self._cached_player_id = first_match.get("player_id", "")

                    self.nickname = first_match.get("nickname", self.nickname)
                else:
                    raise ValueError(f"Игрок '{self.nickname}' вообще не найден на Faceit.")
            else:
                self._cached_player_id = data.get("player_id", "")

        return self._cached_player_id

    def get_player(self) -> Union[dict[str, Any], str]:
        return self._get_json_response(f"players/{self._player_id}")

    def get_player_stats(self) -> str | dict[str, int | str]:
        data = self._get_json_response(f"players/{self._player_id}/games/cs2/stats", params={
            "limit": 100
        })

        if isinstance(data, str):
            return data

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

        winrate = f'{(wins / total_matches) * 100}%' if total_matches > 0 else 0
        KD = f"{(total_kills / (total_deaths + 1)):.2f}" if total_deaths > 0 else 0
        headless_ratio = f'{(total_headshots / total_kills)*100:.0f}%' if total_kills > 0 else 0
        stats = {
            "Matches": total_matches,
            "KD" : KD,
            "Headshots": headless_ratio,
            "Winrate": winrate

        }
        return stats


    def get_player_matches(self) -> Union[dict[str, Any], str]:
        data = self._get_json_response(f"players/{self._player_id}/games/cs2/stats", params={
            "limit": 100
        })
        matches = []
        items = data.get("items", [])
        for item in items:
            match = {}
            stats = item.get("stats", {})
            match['Map'] = stats.get("Map", "")
            match['Win'] = 'Win' if stats.get("Result", 0) else 'Lose'
            match['KD'] = stats.get("K/D Ratio", 0)
            match['Kills'] = stats.get("Kills", 0)
            match['Deaths'] = stats.get("Deaths", 0)
            match['Headshots'] = stats.get("Headshots", 0)
            match['Time'] = stats.get("Updated At", 0)

            matches.append(match)

        return json.dumps(matches, indent=2)


    def __repr__(self) -> str:
        return f"<FaceitPlayer {self.nickname}>"



if __name__ == "__main__":
    player = FaceitPlayer("akkaman1")
    matches = player.get_player_matches()
    stats = player.get_player_stats()
    print(matches + "\n", stats)




