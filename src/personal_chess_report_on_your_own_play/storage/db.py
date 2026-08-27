import duckdb

con = duckdb.connect("data/chessmatchup.duckdb") 

con.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id VARCHAR PRIMARY KEY,
        date DATE,
        time_class STRING,
        rated BOOLEAN,
        my_color STRING,
        my_rating INTEGER,
        opponent_username STRING,
        opponent_rating INTEGER,
        result STRING,
        ECO STRING,
        total_plies INTEGER
    )
""")

def insert_user_games(user):
    for game in user.pgn_games:
        con.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [game.game_id, game.date, game.time_class, game.rated, 
            game.color_played, game.user_rating, game.opponent_username,
            game.opponent_rating, game.result, game.eco, game.total_plies]
        )
    
def show_db():
    con.sql("SELECT * FROM games").show()