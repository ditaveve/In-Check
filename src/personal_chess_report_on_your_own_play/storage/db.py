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
        punishment_line STRING,
        PRIMARY KEY (game_id, ply_number)
    )
""")

con.execute("ALTER TABLE moves ADD COLUMN IF NOT EXISTS punishment_line STRING")

#con.execute("UPDATE games SET analysis_status = 'pending' WHERE game_id = '3e263351-8a7a-11f1-a763-a4cd8501000f';")


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

        # Only keep the punishment_line for actual blunders: below MIN_BLUNDER_THRESHOLD it's
        # noise, and above DECISIVE_EVAL_THRESHOLD it's a mate-score/already-decided-position
        # artifact (same reasoning as the read-time filters on cp_loss elsewhere) -- neither
        # is a real mistake worth an engine-line explanation.
        is_real_blunder = (
            cp_loss is not None and cp_loss >= MIN_BLUNDER_THRESHOLD
            and abs(move['engine_eval']) < DECISIVE_EVAL_THRESHOLD
            and abs(prev_eval) < DECISIVE_EVAL_THRESHOLD
        )
        punishment_line = move['punishment_line'] if is_real_blunder else None

        local_con.execute(
            "INSERT INTO moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [move['game_id'], move['clock_remaining'], move['color'], move['material_balance'],
            move['ply_number'], move['move'], move['engine_eval'], prev_eval, cp_loss,
            punishment_line]
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

def opening_frequency(username, quiet=False):
    # Unlike the cp_loss/blunder metrics, opening choice is treated as one pool across all
    # time_class values rather than split per time control -- players tend to carry the same
    # repertoire across bullet/blitz/rapid, so splitting here would just fragment an already
    # real signal into smaller, noisier per-time-control pieces instead of protecting against
    # a genuine confound (which is what the split is for elsewhere).
    # Grouped by ECO *family* (the leading letter: A/B/C/D/E, ECO's own broad classification)
    # rather than full ECO code -- individual codes like B07/B08/B48 split real overlap between
    # two players into a dozen near-empty rows that each look unremarkable on their own, when
    # together they're a genuine "plays this family often" signal.
    # SUM(COUNT(*)) OVER (PARTITION BY ...) runs after the GROUP BY has already collapsed
    # rows into one per (player_color, family): it sums those per-family counts back up
    # within each player_color partition, giving each row's own share's denominator without
    # a second query.
    # QUALIFY drops whole player_color buckets with too few games to make any percentage
    # meaningful -- otherwise a bucket with 1 total game shows a spurious "100%".
    rel = con.sql('''
        SELECT player_color,
                LEFT(eco, 1) AS eco_family,
                COUNT(*) AS games_in_family,
                COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY player_color) AS frequency
        FROM games
        WHERE tracked_username = ?
        GROUP BY player_color, LEFT(eco, 1)
        QUALIFY SUM(COUNT(*)) OVER (PARTITION BY player_color) >= 5
        ORDER BY player_color, frequency DESC
    ''', params=[username])
    if not quiet:
        rel.show()
    return rel.fetchall()

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

# Once a position is already decisively won/lost, further eval swings aren't real blunders:
# they're either mate-score artifacts (engine_eval/prev_eval converted from mate_score=10000
# in game.py, scaled by moves-to-mate) or, as confirmed by tracing an actual game, shallow-depth
# noise in dead-lost technical endgames (e.g. a bare king being shuffled toward stalemate/mate,
# where the exact cp value swings wildly move to move without reflecting the move's quality).
# Genuine blunders in this data have topped out under ~1300cp, so 2000 leaves headroom for a
# real large blunder while cutting off both kinds of already-decided-position noise.
DECISIVE_EVAL_THRESHOLD = 2000

# Standard chess-analysis convention treats ~200cp+ loss as "blunder" territory (roughly:
# inaccuracy 50-99cp, mistake 100-199cp, blunder 200cp+). Checked against this data: ~7% of
# moves clear 200cp, ~3.8% clear 300cp -- a selective-but-not-vanishingly-rare cut, consistent
# with typical amateur online blunder rates. Below this, storing a punishment_line is just
# noise for a move that wasn't actually a meaningful mistake.
MIN_BLUNDER_THRESHOLD = 200

def biggest_blunders_in_game(game_id):
    con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss, m.punishment_line
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND m.game_id = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """,
        params=[game_id, DECISIVE_EVAL_THRESHOLD, DECISIVE_EVAL_THRESHOLD]
    ).show()

def biggest_blunders(username, time_class, quiet=False):
    # scoped to one time_class: pooling bullet and rapid into a single top-10 would let
    # bullet's naturally noisier play crowd out real blunders from slower time controls.
    rel = con.sql(
        """
        SELECT m.game_id, m.ply_number, m.move, m.cp_loss, m.punishment_line
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND g.tracked_username = ? AND g.time_class = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        ORDER BY m.cp_loss DESC
        LIMIT 10
        """,
        params=[username, time_class, DECISIVE_EVAL_THRESHOLD, DECISIVE_EVAL_THRESHOLD]
    )
    if not quiet:
        rel.show()
    return rel.fetchall()

def avg_cp_loss_by_color(username, quiet=False):
    rel = con.sql( '''
        SELECT g.time_class, g.player_color, AVG(m.cp_loss) AS avg_cp_loss
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE m.color = g.player_color AND g.tracked_username = ?
            AND ABS(m.engine_eval) < ? AND ABS(m.prev_eval) < ?
        GROUP BY g.time_class, g.player_color
    ''', params=[username, DECISIVE_EVAL_THRESHOLD, DECISIVE_EVAL_THRESHOLD])
    if not quiet:
        rel.show()
    return rel.fetchall()

def cp_loss_by_time_pressure(username):
    # opp = the opponent's move immediately before this one (ply_number - 1 is always
    # the other color, since plies strictly alternate), giving their clock at the moment
    # the player made this move.
    rel = con.sql('''
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
    ''', params=[username, DECISIVE_EVAL_THRESHOLD, DECISIVE_EVAL_THRESHOLD])
    rel.show()
    return rel.fetchall()