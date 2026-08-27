from . import chess_data
from . import game

HOW_MANY_GAMES = 200

class User:
    def __init__(self, username):
        self.username = username
        self.archives = chess_data.get_available_archives(self.username)
        self.profile = chess_data.get_user_profile(self.username)
        self.stats = chess_data.get_user_stats(self.username)
        self.games = chess_data.get_user_game_history(self.username, how_many_games=HOW_MANY_GAMES)
        self.pgn_games = []
        for curr_game in self.games:
            pgn_curr_game = chess_data.get_pgn_game(curr_game['pgn'])
            self.pgn_games.append(game.Game(pgn_curr_game, curr_game, username))
