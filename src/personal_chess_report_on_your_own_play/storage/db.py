import duckdb

con = duckdb.connect("data/chessmatchup.duckdb") 

con.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id VARCHAR PRIMARY KEY,
        tracked_username STRING,
        date DATE,
        time_class STRING,
        rated BOOLEAN,
        player_color STRING,
        player_rating INTEGER,
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
            "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [game.game_id, game.player_username, game.date, game.time_class, game.rated, 
            game.color_played, game.user_rating, game.opponent_username,
            game.opponent_rating, game.result, game.eco, game.total_plies]
        )
    
def show_db():
    con.sql("SELECT * FROM games").show()

def win_rate_as_white():
    con.sql( '''
        SELECT player_color, 
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
        FROM games
        GROUP BY player_color
    ''').show()

def win_rate_by_opening():
    con.sql( '''
        SELECT eco, 
                player_color,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
        FROM games
        GROUP BY eco, player_color
        HAVING COUNT(*) >= 5
    ''').show()