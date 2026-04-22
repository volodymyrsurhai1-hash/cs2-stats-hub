import requests
from config import API_FACEIT
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Union
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

    _OFFSET_LIMIT = 200
    _PAGE_SIZE = 100

    def _fetch_all_match_stats(self, game: str = "cs2", period_days: Optional[int] = None) -> list[dict]:
        """Получает всю историю матчей, обходя ограничение offset=200.

        Алгоритм (как в faceitperf):
        - Пока history <= OFFSET_LIMIT: пагинация через offset
        - После OFFSET_LIMIT: пагинация через параметр `to` (Unix timestamp
          последнего загруженного матча), который скользит вглубь истории.
        """
        history: list[dict] = []
        
        cutoff_dt = None
        if period_days:
            cutoff_dt = datetime.now(timezone.utc) - timedelta(days=period_days)

        while True:
            if len(history) <= self._OFFSET_LIMIT:
                params = {"limit": self._PAGE_SIZE, "offset": len(history)}
            else:
                last_ts = history[-1].get("Match Finished At")
                params = {"limit": self._PAGE_SIZE, "to": last_ts}

            data = self._get_json_response(
                f"players/{self._player_id}/games/{game}/stats",
                params=params
            )
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                stats = item.get("stats", {})
                
                # Если задан период, проверяем дату матча
                if cutoff_dt:
                    ts_str = stats.get("Updated At", "")
                    if ts_str:
                        try:
                            match_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if match_dt < cutoff_dt:
                                # Матч старее нужного периода, прекращаем скачивание!
                                return history
                        except (ValueError, TypeError, AttributeError):
                            pass
                            
                history.append(stats)

            if len(items) < self._PAGE_SIZE:
                break

        return history

    def get_player_stats(self, period_days: Optional[int] = None) -> PlayerStats:
        items = self._fetch_all_match_stats(period_days=period_days)
        total_matches = len(items)
        total_kills = 0
        total_deaths = 0
        total_headshots = 0
        wins = 0

        for stats in items:
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


    @staticmethod
    def _format_timestamp(ts: str) -> str:
        """Конвертирует ISO 8601 строку в читаемый вид: '22 Apr 2025'."""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y")
        except (ValueError, TypeError, AttributeError):
            return ts or "—"

    def get_player_matches(self, period_days: Optional[int] = None) -> list[MatchRecord]:
        items = self._fetch_all_match_stats(period_days=period_days)
        return [
            MatchRecord(
                map=s.get("Map", ""),
                win=s.get("Result") == "1",
                kd=s.get("K/D Ratio", "0"),
                kills=int(s.get("Kills", 0)),
                deaths=int(s.get("Deaths", 0)),
                headshots=int(s.get("Headshots", 0)),
                played_at=self._format_timestamp(s.get("Updated At", "")),
            )
            for s in items
        ]


    def __repr__(self) -> str:
        return f"<FaceitPlayer {self.nickname}>"



if __name__ == "__main__":
    player = FaceitPlayer("matb_shluyxa")
    stats = player.get_player_stats()
    print(f"Всего матчей: {stats.matches}")
    print(stats.as_display())
    print(player.get_player_matches())
