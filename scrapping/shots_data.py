from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import shotchartdetail
import json
import pandas as pd
import time
import requests
import datetime
from db_functions import save_to_csv, save_to_mongo
from typing import List, Dict

from variables import HEADERS, COLUMNS

START_YEAR = 2010
END_YEAR = datetime.datetime.today().year
TIMEOUT = 1.2
SAVE_DB = 'mongodb'
COLLECTION = 'shots'

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
    for i in range(START_YEAR, END_YEAR + 1):
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
    time.sleep(TIMEOUT)
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
    df_shots = pd.DataFrame(columns=COLUMNS)
    for i in range(START_YEAR, END_YEAR + 1):
        season_start = i
        season_end = i+1
        season = str(season_start) + "-" + str(season_end)[-2:]
        players = players_by_season[season]
        df_shots_year = get_season_shotchart(season, players)
        df_shots_year = format_df(df_shots_year, season)
        print(f"Shot chart of season {season} obtained!")
        df_shots = pd.concat([df_shots, df_shots_year])
    return df_shots


def format_df(df: pd.DataFrame, season: str) -> pd.DataFrame:
    df["season"] = season
    df["timestamp"] = datetime.datetime.now()
    df["_id"] = df["GAME_ID"].astype(str) + "_" + df["GAME_EVENT_ID"].astype(str)
    return df

def load_from_csv(path='data/') -> pd.DataFrame:
    df = pd.DataFrame()
    for i in range(START_YEAR, END_YEAR + 1):
        season_start = i
        season_end = i+1
        season = str(season_start) + "-" + str(season_end)[-2:]
        filename = path + 'shotchart_' + season + '.csv'
        df_year = pd.read_csv(filename)
        df_year = df_year.drop('Unnamed: 0', axis=1)
        df_year = format_df(df_year, season)
        df = pd.concat([df, df_year])
    return df

def save_data(df):
    if SAVE_DB == 'mongodb':
        save_to_mongo(df)
    elif SAVE_DB == 'csv':
        file_name = 'shotchart' + '_' + START_YEAR + '_' + END_YEAR
        save_to_csv(df, file_name)
    return True

if __name__ == "__main__":
    players_by_season = get_players()
    print("Players list obtained!")
    shot_chart = get_shotchart(players_by_season)
    print("All shot charts obtained!")
    save_to_mongo("shots", df)
    print("Data inserted in mongodb!")
