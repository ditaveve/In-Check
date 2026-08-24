import json
from pathlib import Path

USER_PATH="src/user_data"

def is_user_cached(username):
    user_path = Path("src/user_data") / username
    return user_path.is_dir()

def create_user_folder(username):
    user_path = Path("src/user_data") / username
    user_path.mkdir()
    return user_path

def create_archives_folder(username):
    archives_path = Path("src/user_data/") / username / "archives"
    archives_path.mkdir()
    return archives_path

def update_user_profile(username, profile_data):
    user_path = Path(f"src/user_data/{username}")
    profile_path = user_path / "profile.json"
    with open(profile_path, 'w') as file:
        json.dump(profile_data, file, indent=2)

def update_user_stats(username, stats_data):
    user_path = Path(f"src/user_data/{username}")
    stats_path = user_path / "stast.json"
    with open(stats_path, 'w') as file:
        json.dump(stats_data, file, indent=2)

def get_cached_user_profile(username):
    """Load a user's profile data from the local cache."""
    with open(f"{USER_PATH}/{username}/profile.json", 'r') as file:
        return json.load(file)

def get_cached_user_stats(username):
    """Load a user's stats data from the local cache."""
    with open(f"{USER_PATH}/{username}/stats.json", 'r') as file:
        return json.load(file)
    