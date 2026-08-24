import requests
import os
from dotenv import load_dotenv


load_dotenv()
HEADERS = {
    "User-Agent": f"personal-chess-report-on-your-own-play (contact: {os.getenv("CONTACT_EMAIL")})"
}

def get_monthly_games(username, YYYY, MM):
    url = f"https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM:0>2}"
    response = requests.get(url, headers=HEADERS)
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to retrieve data.")