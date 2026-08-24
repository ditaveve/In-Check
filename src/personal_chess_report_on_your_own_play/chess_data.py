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
    if response.status_code == 200:
        data = response.json()
        return data['archives']
    else:
        print("Failed to retrieve all archives.")

def get_monthly_games(monthly_arhive_url):
    response = requests.get(monthly_arhive_url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to retrieve monthly games.")

def get_game_history(username, how_many_games):
    all_archives = get_available_archives(username)[::-1]
    all_games = []
    while how_many_games:
        for monthly_archive_url in all_archives:
            monthly_archives = get_monthly_games(monthly_archive_url)['games']
            for game in monthly_archives:
                print(game)
                how_many_games -= 1
                if how_many_games <= 0:
                    return
    return all_games