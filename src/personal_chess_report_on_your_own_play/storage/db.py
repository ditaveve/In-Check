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
        total_plies INTEGER,
        analysis_status STRING
    )
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS moves (
        game_id VARCHAR,
        clock_remaining DOUBLE,
        color STRING,
        material_balance INTEGER,
        ply_number INTEGER,
        move STRING,
        engine_eval DOUBLE,
        prev_eval DOUBLE,
        cp_loss DOUBLE,
        PRIMARY KEY (game_id, ply_number)
    )
""")

con.execute("ALTER TABLE moves ADD COLUMN IF NOT EXISTS prev_eval " \
            "DOUBLE DEFAULT 0")

def insert_game_moves(analysed_game_data):
    local_con = con.cursor()
    prev_eval = None
    for move in analysed_game_data:
        if prev_eval is None:
            cp_loss = None
        elif move['color'] == 'white':
            cp_loss = prev_eval - move['engine_eval']
        else:
            cp_loss = move['engine_eval'] - prev_eval
        local_con.execute(
            "INSERT INTO moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [move['game_id'], move['clock_remaining'], move['color'], move['material_balance'], 
            move['ply_number'], move['move'], move['engine_eval'], prev_eval, cp_loss]
        )
        prev_eval = move['engine_eval']


def insert_user_games(user):
    local_con = con.cursor()
    for game in user.pgn_games:
        local_con.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [game.game_id, game.player_username, game.date, game.time_class, game.rated, 
            game.color_played, game.user_rating, game.opponent_username,
            game.opponent_rating, game.result, game.eco, game.total_plies, 'pending']
        )
    
def show_games_db():
    con.sql("SELECT * FROM games").show()

def show_moves_db():
    con.sql("SELECT * FROM moves").show()

def delete_games_db():
    con.sql("DROP TABLE games")

def delete_moves_db():
    con.sql("DROP TABLE moves")

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

def games_still_pending():
    rows = con.sql("SELECT game_id FROM games WHERE analysis_status = 'pending' ").fetchall()
    return [row[0] for row in rows]

def update_analysis_state(game_id):
    con.execute("UPDATE games SET analysis_status = 'complete' WHERE game_id = ?", [game_id])

def biggest_blunders_in_game(game_id):
    con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND m.game_id = ?
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """,
        params=[game_id]
    ).show()

def biggest_blunders():
    con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """
    ).show()