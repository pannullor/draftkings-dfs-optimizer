import argparse
import pprint
import sys, os
import json
from json.decoder import JSONDecodeError
import datetime
import requests

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
from dfs.mapping import get_session, Player, Slate, Contest, PlayerOwnership, Entry, Lineup

import time
import traceback


def transform_date(d):
    """
    converts datetime to naive YYYY-MM-DD HH:MM:SS format

    :returns: DateTime
    """
    return datetime.datetime.fromisoformat(d[:-1]).replace(tzinfo=None)


def make_request(endpoint, params):
    # headers for the request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'referer': 'https://rotogrinders.com/'
    }

    url = f"https://resultsdb-api.rotogrinders.com/api/{endpoint}"

    r = requests.get(url, params=params, headers=headers)
    if r.status_code == 200:
        return r.json()

    return None


def get_or_create_player(session, player_data):
    player_ = session.query(Player).filter(Player.player_id == player_data['player_id']).all()
    print(player_)
    if player_:
        created = False
    else:
        player_ = Player(**player_data)
        session.add(player_)
        session.commit()
        created = True

    return player_, created


def fetch_slates(event_date, slate_type):
    """
    Fetches slates PGA Tour event slates for the given date
    """

    # db connection object
    session = get_session()

    # slate URL with the event date formatted
    slate_params = {
        'start': event_date,
        'site': 20
    }

    # make the request to the endpoint to
    # gather the slate data.This will give
    # us players, game (slate) type, and
    # an ID to fetch the results.
    slates = make_request("slates", slate_params)
    if slates:
        # filter the results to the golf slats of the type requests
        slates = list(filter(lambda x: x['slateType'] == slate_type and x['sport'] == 6, slates))

        slate_ids = []
        for slate_ in slates:
            slate_ids.append(slate_["_id"])
            session.add(
                Slate(
                    **{
                        'slate_id': slate_["_id"],
                        'slate_type': slate_["slateType"],
                        'slate_type_name': slate_["slateTypeName"],
                        'sport': slate_["sport"],
                        'start_date': transform_date(slate_["start"]),
                        'end_date': transform_date(slate_["end"])
                    }
                )
            )
            session.commit()
            print("slate added")

        contests_params = {
            'slates': ','.join(slate_ids),
            'lean': 'true'
        }

        contests = make_request("contests", contests_params)
        # use the contest IDs to get the contests in the slate.
        # from the contests we can get the entries and lineups.
        for contest_ in contests:
            contest_id = contest_["_id"]

            session.add(
                Contest(
                    **{
                        'contest_id': contest_id,
                        'slate_fk': contest_["_slateId"],
                        'prize_pool': contest_["prizePool"],
                        'max_entries': contest_['maxEntries'],
                        'max_entries_per_user': contest_['maxEntriesPerUser'],
                        'entry_fee': contest_['entryFee'],
                        'name': contest_['name']
                    }
                )
            )
            session.commit()
            print(F"Contest {contest_id} added. Adding Player and Entry data.")

            # params for an individual contest one we have the ID
            contest_params = {"_id": contest_id, "ownership": "true"}
            contest_results = make_request("contests", contest_params)

            # for this contest get the ownership
            if contest_results:
                # all the players in the contest. Only extract the data we need.
                for player_ in contest_results[0]["playerOwnership"]:
                    player_data = {
                        'player_id': player_["siteSlatePlayerId"],
                        'name': player_["name"],
                    }

                    new_player, created = get_or_create_player(session, player_data)
                    if created:
                        print(f"{player_['name']} already inserted")
                    else:
                        print(f"Created player {player_['name']}")

                    session.add(
                        PlayerOwnership(
                            **{
                                'slate_player_id': player_['_id'],  # ID only exists within the slate
                                'player_fk': player_["siteSlatePlayerId"],
                                'contest_fk': contest_id,
                                'salary': player_['salary'],
                                'projected_ownership': player_.get('projectedOwnership', None),
                                'actual_ownership': player_.get('actualOwnership', None),
                                'projected_fantasy_points': player_.get('projectedFpts', None),
                                'actual_fantasy_points': player_.get('actualFpts', None)
                            }
                        )
                    )
                    session.commit()

                    print(f"Successfully added {player_['name']} to PlayerOwnership")

                # now get the entries for each contest
                # Entries are paginated.
                index = 0
                while True:
                    entry_params = {
                        '_contestId': contest_id,
                        'sortBy': 'points',
                        'order': 'desc',
                        'index': index,
                        'users': 'false'
                    }
                    entries = make_request("entries", entry_params)

                    if entries:
                        for entry_ in entries['entries']:
                            session.add(
                                Entry(
                                    **{
                                        'entry_id': entry_["_id"],
                                        'contest_fk': contest_id,
                                        'rank': entry_['rank'],
                                        'points': entry_['points'],
                                    }
                                )
                            )
                            session.commit()
                            print(f"Entry for contest {contest_id} added")

                            # add this lineup
                            for lineup_ in entry_['lineup']["G"]:

                                session.add(
                                    Lineup(
                                        **{
                                            'entry_fk': entry_["_id"],
                                            'playerownership_fk': lineup_["_slatePlayerId"]
                                        }
                                    )
                                )
                                session.commit()
                                print(f"LINEUP added for entry {entry_['_id']} playerownership: {lineup_['_slatePlayerId']}")
                        index += 1
                    else:
                        break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Event date to fetch slates')

    parser.add_argument('event_date', type=str, help='Event Start Date')
    parser.add_argument('slate_type', type=int, help='Event Slate Type')

    args = parser.parse_args()

    fetch_slates(args.event_date, args.slate_type)
