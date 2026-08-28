import pytest
from unittest.mock import patch, MagicMock

# Мокаем config до импорта api_cs2, чтобы не падали тесты без .env файла на CI
with patch("config.API_FACEIT", "dummy_token"):
    from api_cs2 import FaceitPlayer, FaceitAPIError, PlayerStats

@pytest.fixture
def mock_requests_get():
    # Мокаем библиотеку requests, чтобы не делать реальных вызовов в Faceit API
    with patch("api_cs2.requests.get") as mock_get:
        yield mock_get

def test_get_player_id_success(mock_requests_get):
    # Настраиваем фейковый ответ от API
    mock_response = MagicMock()
    mock_response.json.return_value = {"player_id": "test_123"}
    mock_requests_get.return_value = mock_response

    player = FaceitPlayer("test_nick")
    
    # Действие
    pid = player._player_id
    
    # Проверки
    assert pid == "test_123"
    mock_requests_get.assert_called_once()
    assert "players" in mock_requests_get.call_args[0][0] # проверяем, что эндпоинт верный

def test_get_player_stats(mock_requests_get):
    # モкаем _get_json_response напрямую
    with patch.object(FaceitPlayer, "_get_json_response") as mock_json:
        # Фейковая история матчей
        mock_json.return_value = {
            "items": [
                {
                    "stats": {
                        "Kills": "10", 
                        "Deaths": "5", 
                        "Headshots": "5", 
                        "Result": "1"
                    }
                }
            ]
        }
        
        player = FaceitPlayer("test_nick")
        stats = player.get_player_stats() 

        assert stats.matches == 1
        assert stats.kd_ratio == 2.0
        assert stats.headshot_pct == 50.0
        assert stats.winrate_pct == 100.0
