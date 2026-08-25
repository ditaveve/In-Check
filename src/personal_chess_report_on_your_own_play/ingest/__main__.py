from . import chess_data
from . import game
from . import user
from .user import User

def main() -> None:
    my_user = User('ditaveve')
    for my_game in my_user.pgn_games:
        print(f"{my_game.pgn}\n")

if __name__ == "__main__":
    main()