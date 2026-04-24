import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from django.shortcuts import render
from api_cs2 import FaceitPlayer, FaceitAPIError


def index(request):
    nickname = request.GET.get("nickname", "").strip()
    period = request.GET.get("period", "30")
    
    # Mapping periods to days
    days_map = {
        "30": 30,
        "90": 90,
        "365": 365,
        "all": None
    }
    period_days = days_map.get(period, None)

    context = {
        "nickname": nickname,
        "period": period
    }

    if nickname:
        try:
            player = FaceitPlayer(nickname)
            info    = player.get_player()
            stats   = player.get_player_stats(period_days=period_days)
            matches = player.get_player_matches(period_days=period_days)

            context.update({
                "nickname":   player.nickname,
                "avatar":     info.get("avatar", ""),
                "country":    info.get("country", ""),
                "elo":        info.get("games", {}).get("cs2", {}).get("faceit_elo", "—"),
                "level":      info.get("games", {}).get("cs2", {}).get("skill_level", "—"),
                "stats":      stats,
                "matches":    matches,
            })
        except FaceitAPIError as e:
            context["error"] = f"Faceit API error {e.status_code}: {e}"
        except ValueError as e:
            context["error"] = str(e)
        except Exception as e:
            context["error"] = f"Unexpected error: {e}"

    return render(request, "viewer_stats/index.html", context)

def match_room(request, match_id):
    context = {"match_id": match_id}
    try:
        player = FaceitPlayer("dummy")
        teams = player.get_room_of_match(match_id)
        
        # Calculate +/- and other derived stats if necessary
        for team in teams:
            for p in team.players:
                try:
                    p.plus_minus = int(p.kills) - int(p.deaths)
                except ValueError:
                    p.plus_minus = 0
            
            # Sort players by KD ratio (descending)
            team.players.sort(key=lambda p: float(p.kd) if p.kd else 0.0, reverse=True)

        context["teams"] = teams
    except FaceitAPIError as e:
        context["error"] = f"Faceit API error {e.status_code}: {e}"
    except Exception as e:
        context["error"] = f"Unexpected error: {e}"

    return render(request, "viewer_stats/match_room.html", context)