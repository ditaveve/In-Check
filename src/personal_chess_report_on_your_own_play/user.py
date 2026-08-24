from . import cache
from . import chess_data

class User:
    def __init__(self, username):
        if not cache.is_user_cached():
            self.username = username
        else:
            raise Exception("This user already exists")
