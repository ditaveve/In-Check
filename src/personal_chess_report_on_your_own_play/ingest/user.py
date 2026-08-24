from . import chess_data

class User:
    def __init__(self, username):
        self.username = username
        self.archives = chess_data.get_available_archives(username)
        self.profile = chess_data.get_user_profile(username)
        self.stats = chess_data.get_user_stats(username)
