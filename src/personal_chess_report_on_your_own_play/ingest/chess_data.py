import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

BASE_URL="https://api.chess.com/pub/player"
HEADERS = {
    "User-Agent": f"personal-chess-report-on-your-own-play (contact: {os.getenv("CONTACT_EMAIL")})"
}

def get_available_archives(username):
    """Fetch the list of monthly archive URLs available for a Chess.com user."""
    all_archives_url = f"{BASE_URL}/{username}/games/archives"
    response = requests.get(all_archives_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data['archives']

def get_monthly_games(username, YYYY, MM):
    """Fetch all games from a single monthly archive."""
    monthly_archive_url = f"{BASE_URL}/{username}/games/{YYYY}/{MM}"
    response = requests.get(monthly_archive_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def get_user_game_history(username, how_many_games):
    """Collect the user's most recent games, newest archive first, up to how_many_games."""
    all_archives = get_available_archives(username)[::-1]
    all_games = []
    while how_many_games:
        for monthly_archive_url in all_archives:
            response = requests.get(monthly_archive_url, headers=HEADERS)
            response.raise_for_status()
            monthly_archives = response.json()['games']
            for game in monthly_archives:
                all_games.append(game)
                how_many_games -= 1
                if how_many_games <= 0:
                    return all_games
    return all_games

def get_user_profile(username):
    profile_url = f"{BASE_URL}/{username}"
    response = requests.get(profile_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def get_user_stats(username):
    stats_url = f"{BASE_URL}/{username}/stats"
    response = requests.get(stats_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data
