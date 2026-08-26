from .game import get_user_result
from .chess_data import get_pgn_game
from .user import User
from pathlib import Path
import pytest


TESTER_DIR = Path(__file__).parent / "tester"

@pytest.fixture
def won_by_white():
    with open(TESTER_DIR / 'won_game_by_white.txt', 'r') as file:
            return get_pgn_game(file.read())
@pytest.fixture
def won_by_black():
    with open(TESTER_DIR / 'won_game_by_black.txt', 'r') as file:
            return get_pgn_game(file.read())
    
@pytest.fixture
def game_drawn():
    with open(TESTER_DIR / 'draw_game.txt', 'r') as file:
            return get_pgn_game(file.read())


def test_white_wins(won_by_white):
    assert get_user_result(won_by_white, 'white') == "win"
    assert get_user_result(won_by_white, 'black') == "loss"
    
def test_black_wins(won_by_black):
    assert get_user_result(won_by_black, 'black') == "win"
    assert get_user_result(won_by_black, 'white') == "loss"

def test_draw(game_drawn):
    assert get_user_result(game_drawn, 'white') == "draw"
    assert get_user_result(game_drawn, 'black') == "draw"

    