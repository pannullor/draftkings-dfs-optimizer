import json
from json.decoder import JSONDecodeError
import pandas as pd
import datetime
import requests
import csv
from bs4 import BeautifulSoup
import sys, os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
from dfs.mapping import get_connection, player, slate, contest, draftgroup

import pprint
import time
import traceback

"""
This script will fetch the available DraftKings slates from RotoGrindersDB
for the 2020-21 PGA Tour season. It will populate 
"""

def transform_date(d):
    """
    converts datetime to naive YYYY-MM-DD HH:MM:SS format

    :returns: DateTime
    """
    return datetime.datetime.fromisoformat(d[:-1]).replace(tzinfo=None)

def fetch_slates():
    """
    Fetches slates for 2020-21 PGA Tour season
    """

    # db connection object
    conn = get_connection()

    # necessary to have the referer in the headers or else
    # we get a 403, the is generated when the site loads so
    # just grab it from the developer console.
    referer_key = "5f5a33125efd8359983dc8e5"
    referer_url = f"https://rotogrinders.com/resultsdb/site/draftkings/date/2020-09-10/sport/golf/slate/{referer_key}"

    # headers for the request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'referer': referer_url
    }

    # very first event in the season. Loop through all the events, the last
    # was 09/02/21, and gather whatever slates are available from RotoGrinders
    event_date = datetime.datetime.strptime("2020-09-10", "%Y-%m-%d")
    slates = []
    while True:
        slate_date = event_date.strftime("%m/%d/%Y")
        slate_url = f"https://resultsdb-api.rotogrinders.com/api/slates?start={slate_date}&site=20"
        r = requests.get(slate_url, headers=headers)

        # filter the slates to just the golf ones and collect what we can
        slate_ids = []
        try:
            slates = r.json()
        except JSONDecodeError as err:
            if r.status_code == 200:
                slates = json.loads(str(r.content))
            else:
                print(f"SLATES JSON STATUS CODE: {r.status_code}")
                slates = []
        
        try:
            for slate_ in list(filter(lambda x: x["sport"] == 6, slates)):
                draftgroup_id = slate_['siteSlateId']
                slate_id = slate_['_id']
                slate_ids.append(slate_id)

                slate_data = {
                    'slate_id': slate_id,
                    'slate_draftgroup_id': draftgroup_id,
                    'start_date': transform_date(slate_['start']),
                    'end_date': transform_date(slate_['end']),
                    'sport': 6,
                    'slate_type': slate_['slateType']
                }
                conn.execute(slate.insert().values(slate_data))
                print(f"Succesfully inserted slate {slate_id}")

                # hit the DK draftables api endpoint to
                # get all the players for each slate
                dk_url = f"https://api.draftkings.com/draftgroups/v1/draftgroups/{draftgroup_id}/draftables"
                r2 = requests.get(dk_url)
                for draftable in r2.json()['draftables']:
                    player_data = {
                        'player_id': draftable['playerId'],
                        'first_name': draftable['firstName'],
                        'last_name': draftable['lastName']
                    }
                    conn.execute(player.insert().values(player_data))
                    print(f"Succesfully inserted player {player_data['player_id']}")
                    
                    draftable_id = draftable['draftableId']
                    slate_player = list(filter(lambda x: int(x['siteSlatePlayerId']) == draftable_id, slate_['slatePlayers']))[0]
                    avg_fantasy_points = list(filter(lambda x: x['id'] == 795, draftable['draftStatAttributes']))[0]['value']
                    try:
                        avg_fantasy_points = float(avg_fantasy_points)
                    except Exception as err:
                        avg_fantasy_points = -1.0

                    try:
                        salary = float(draftable['salary'])
                    except Exception as err:
                        salary = -1.0

                    draftgroup_data = {
                        'draftable_id': draftable_id,
                        'salary': salary,
                        'average_fantasy_points': avg_fantasy_points,
                        'projected_fantasy_points': slate_player.get('projectedFpts', None),
                        'slate_draftgroup_fk': draftgroup_id,
                        'player_fk': draftable['playerId'],
                    }
                    conn.execute(draftgroup.insert().values(draftgroup_data))
                    print(f"Succesfully inserted draftgrop {draftable_id}")
            
            # gather up the contests now.
            contests_url = "https://resultsdb-api.rotogrinders.com/api/contests"
            params = {'slates': ','.join(slate_ids), 'lean': 'true'}
            r3 = requests.get(contests_url, params=params, headers=headers)
            try:
                try:
                    contests = r3.json()
                except JSONDecodeError as err:
                    if r3.status_code == 200:
                        contests = json.loads(str(r3.content))
                    else:
                        print(f"CONTESTS JSON STATUS CODE: {r3.status_code}")
                        contests = []
                
                for contest_ in contests:
                    contest_data = {
                        'contest_id': contest_['siteContestId'],
                        'name': contest_['name'],
                        'start_date': transform_date(contest_['start']),
                        'max_entries_per_user': contest_.get('maxEntriesPerUser', None),
                        'max_entries': contest_.get('maxEntries', None),
                        'total_entries': contest_.get('entryCount', None),
                        'slate_fk': contest_['_slateId']
                    }
                    conn.execute(contest.insert().values(contest_data))
                    print(f"Succesfully inserted contest {contest_data['contest_id']}")
            except Exception as err:
                print(f"CONTESTS STATUS CODE: {r3.status_code}")
                traceback.print_exc()

        except Exception as err:
            traceback.print_exc()

        event_date = event_date + datetime.timedelta(days=7)
        if event_date > datetime.datetime.strptime("2021-09-02", "%Y-%m-%d"):
            break

        print(f"NEW EVENT DATE: {event_date}")
        time.sleep(2)
    
    print("Succesfully imported 2020-21 PGA Season DraftKings Slates")

if __name__ == "__main__":

    fetch_slates()