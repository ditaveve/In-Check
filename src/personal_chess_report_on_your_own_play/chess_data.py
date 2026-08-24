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
        return data
    else:
        print("Failed to retrieve all archives.")

def get_monthly_games(username, YYYY, MM):
    monthly_arhive_url = f"{BASE_URL}/{username}/games/{YYYY}/{MM}"
    response = requests.get(monthly_arhive_url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to retrieve monthly games.")
