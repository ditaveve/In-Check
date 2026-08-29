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
    
def show_games_db(username):
    con.sql("SELECT * FROM games WHERE tracked_username = ?", params=[username]).show()

def show_moves_db(username):
    con.sql('''
        SELECT m.*
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE g.tracked_username = ?
    ''', params=[username]).show()

def delete_games_db():
    con.sql("DROP TABLE games")

def delete_moves_db():
    con.sql("DROP TABLE moves")

def win_rate_as_white(username):
    con.sql( '''
        SELECT time_class,
                player_color,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
        FROM games
        WHERE tracked_username = ?
        GROUP BY time_class, player_color
    ''', params=[username]).show()

def win_rate_by_opening(username):
    con.sql( '''
        SELECT time_class,
                eco,
                player_color,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS win_rate
        FROM games
        WHERE tracked_username = ?
        GROUP BY time_class, eco, player_color
        HAVING COUNT(*) >= 5
    ''', params=[username]).show()

def games_still_pending():
    rows = con.sql("SELECT game_id FROM games WHERE analysis_status = 'pending' ").fetchall()
    return [row[0] for row in rows]

def time_classes_played(username):
    rows = con.sql(
        "SELECT DISTINCT time_class FROM games WHERE tracked_username = ?",
        params=[username]
    ).fetchall()
    return [row[0] for row in rows]

def update_analysis_state(game_id):
    con.execute("UPDATE games SET analysis_status = 'complete' WHERE game_id = ?", [game_id])

# engine_eval/prev_eval are converted from mate scores using mate_score=10000 in game.py,
# scaled down by moves-to-mate (e.g. mate in 3 -> 9997), so real mate scores land in
# [9000, 10000] rather than exactly at 10000. Excluding |eval| >= 9000 drops mate-transition
# rows (whose cp_loss is a meaningless artifact of that constant) without touching real evals.
MATE_EVAL_THRESHOLD = 9000

def biggest_blunders_in_game(game_id):
    con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND m.game_id = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """,
        params=[game_id, MATE_EVAL_THRESHOLD, MATE_EVAL_THRESHOLD]
    ).show()

def biggest_blunders(username, time_class):
    # scoped to one time_class: pooling bullet and rapid into a single top-10 would let
    # bullet's naturally noisier play crowd out real blunders from slower time controls.
    con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND g.tracked_username = ? AND g.time_class = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """,
        params=[username, time_class, MATE_EVAL_THRESHOLD, MATE_EVAL_THRESHOLD]
    ).show()

def avg_cp_loss_by_color(username):
    con.sql( '''
        SELECT g.time_class, g.player_color, AVG(m.cp_loss) AS avg_cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND g.tracked_username = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        GROUP BY g.time_class, g.player_color
    ''', params=[username, MATE_EVAL_THRESHOLD, MATE_EVAL_THRESHOLD]).show()

def cp_loss_by_time_pressure(username):
    # opp = the opponent's move immediately before this one (ply_number - 1 is always
    # the other color, since plies strictly alternate), giving their clock at the moment
    # the player made this move.
    con.sql('''
        SELECT
            g.time_class,
            CASE WHEN m.clock_remaining < 30 THEN 'under 30s' ELSE 'everything else' END AS time_bucket,
            CASE
                WHEN opp.clock_remaining IS NULL THEN 'unknown'
                WHEN m.clock_remaining < opp.clock_remaining THEN 'behind on clock'
                ELSE 'ahead or even'
            END AS clock_diff_bucket,
            AVG(m.cp_loss) AS avg_cp_loss,
            COUNT(*) AS total_moves
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        LEFT JOIN moves opp ON opp.game_id = m.game_id AND opp.ply_number = m.ply_number - 1
        WHERE m.color = g.player_color AND g.tracked_username = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        GROUP BY g.time_class, time_bucket, clock_diff_bucket
    ''', params=[username, MATE_EVAL_THRESHOLD, MATE_EVAL_THRESHOLD]).show()