import json
from pathlib import Path

def is_user_cached(username):
    user_path = Path("src/user_data") / username
    return user_path.is_dir()

def create_user_folder(username):
    user_path = Path("src/user_data") / username
    user_path.mkdir()
    return user_path

def setup_user_profile(username, profile_data):
    user_path = Path(f"src/user_data/{username}")
    profile_path = user_path / "profile.json"
    if profile_path.exists():
        update_user_profile(username, profile_data)
    with open(profile_path, 'w') as file:
        json.dump(profile_data, file, indent=2)

def setup_user_stats(username, stats_data):
    user_path = Path(f"src/user_data/{username}")
    stats_path = user_path / "stast.json"
    if stats_path.exists():
        update_user_stats(username, stats_data)
    with open(stats_path, 'w') as file:
        json.dump(stats_data, file, indent=2)

def update_user_profile(username, profile_data):
    pass

def update_user_stats(username, stats_data):
    pass