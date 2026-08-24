import requests
import os
from dotenv import load_dotenv

BASE_URL="https://api.chess.com/pub/player"

load_dotenv()
HEADERS = {
    "User-Agent": f"personal-chess-report-on-your-own-play (contact: {os.getenv("CONTACT_EMAIL")})"
}

def get_available_archives(username):
    all_archives_url = f"{BASE_URL}/{username}/games/archives"
    response = requests.get(all_archives_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data['archives']

def get_monthly_games(monthly_arhive_url):
    response = requests.get(monthly_arhive_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def get_game_history(username, how_many_games):
    all_archives = get_available_archives(username)[::-1]
    all_games = []
    while how_many_games:
        for monthly_archive_url in all_archives:
            monthly_archives = get_monthly_games(monthly_archive_url)['games']
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
