from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import shotchartdetail
import json
import pandas as pd
import time
import requests
import datetime
from functions import save_to_csv
from typing import List, Dict

HEADERS = {
    'Host': 'stats.nba.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

COLUMNS = ['GRID_TYPE', 'GAME_ID', 'GAME_EVENT_ID', 'PLAYER_ID', 'PLAYER_NAME',
       'TEAM_ID', 'TEAM_NAME', 'PERIOD', 'MINUTES_REMAINING',
       'SECONDS_REMAINING', 'EVENT_TYPE', 'ACTION_TYPE', 'SHOT_TYPE',
       'SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE', 'SHOT_DISTANCE',
       'LOC_X', 'LOC_Y', 'SHOT_ATTEMPTED_FLAG', 'SHOT_MADE_FLAG', 'GAME_DATE',
       'HTM', 'VTM']

START_YEAR = 2011
END_YEAR = datetime.datetime.today().year


def get_content_df(content: Dict) -> pd.DataFrame:
    results = content['resultSets'][0]
    headers = results['headers']
    rows = results['rowSet']
    df = pd.DataFrame(rows)
    df.columns = headers
    return df


def get_season_players(season: str) -> List[int]:
    response = commonallplayers.CommonAllPlayers(
        season = season,
        league_id = "00"
    )
    time.sleep(0.9)
    content = json.loads(response.get_json())
    players = get_content_df(content)
    players = players[players['ROSTERSTATUS']==1]['PERSON_ID']
    return players


def get_players() -> Dict:
    players_by_season = {}
    for i in range(START_YEAR, END_YEAR):
        season_start = i
        season_end = i+1
        season = str(season_start) + "-" + str(season_end)[-2:]
        print(f"-----PLAYERS LIST SEASON {season}-----")
        players = get_season_players(season)
        players_by_season[season] = players
    return players_by_season


def get_player_shotchart(player: int, season: str) -> pd.DataFrame:
    response = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=player,
        season_nullable=season,
        context_measure_simple= 'FGA',
        league_id="00",
    )
    time.sleep(0.9)
    try:
        content = json.loads(response.get_json())
        player_shots = get_content_df(content)
        return player_shots
    except:
        return None


def get_season_shotchart(season: str, players: List[int]) -> pd.DataFrame:
    print(f"-------SHOTCHART SEASON {season}-------")
    df_shots = pd.DataFrame()
    players_obtained = 0
    for player in players:
        df_player_shots = get_player_shotchart(player, season)
        if df_player_shots is not None:
            players_obtained += 1
            df_shots = pd.concat([df_shots, df_player_shots])
            # shots.append(player_shots)
            if players_obtained % 10 == 0:
                print(f"Player {players_obtained}...")
    return df_shots


def get_shotchart(players_by_season: Dict) -> pd.DataFrame:
    for i in range(START_YEAR, END_YEAR):
        season_start = i
        season_end = i+1
        season = str(season_start) + "-" + str(season_end)[-2:]
        players = players_by_season[season]
        df_shots = get_season_shotchart(season, players)
        try:
            save_to_csv(df_shots, "shotchart_" + season + ".csv")
        except Exception:
            raise Exception(f"Could no save season {season} shot chart")
        print(f"Shot chart of season {season} obtained!")
    return df_shots


if __name__ == "__main__":
    players_by_season = get_players()
    # print(players_by_season)
    print("Players list obtained!")
    shot_chart = get_shotchart(players_by_season)
    print("All shot charts obtained!")
