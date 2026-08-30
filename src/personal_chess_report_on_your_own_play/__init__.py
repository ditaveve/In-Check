from .ingest import chess_data
from .ingest import game
from .ingest import user
from .ingest.user import User
from .ingest.user import HOW_MANY_GAMES
from .storage import db
from .features.report import MatchupReport
from concurrent.futures import ThreadPoolExecutor
import os
import time
    

def ingest_users_games(usernames):
    """Fast: fetch each user's recent PGNs from Chess.com and insert pending rows."""
    users = [User(username) for username in usernames]
    for u in users:
        db.insert_user_games(u)
    return users

def analyse_pending_games(users):
    """Slow: run Stockfish on whichever of these users' games are still pending."""
    all_games = [g for u in users for g in u.pgn_games]
    pending_games = db.games_still_pending()
    new_games = [g for g in all_games if g.game_id in pending_games]

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(game.Game.walk_through, new_games))
        list(executor.map(db.insert_game_moves, results))
    for g in new_games:
        db.update_analysis_state(g.game_id)

TRACKED_USERNAMES = ['ditaveve', 'ThePieceTaker99']

def check_pending() -> None:
    """Fast: fetch new games and report how many are queued for analysis, without running Stockfish."""
    ingest_users_games(TRACKED_USERNAMES)
    print(f"{len(db.games_still_pending())} games pending analysis")

def main() -> None:
    start = time.perf_counter()
    my_user, david_user = ingest_users_games(TRACKED_USERNAMES)
    analyse_pending_games([my_user, david_user])

    MatchupReport(my_user.username, david_user.username).generate()

    print(f"Took {time.perf_counter() - start:.2f}s")

if __name__ == "__main__":
    main()
