import chess.pgn
import chess
import chess.engine
import shutil

def get_game_eco(game_pgn):
    return game_pgn.headers['ECO']

def get_user_color(game_pgn, username):
    if username == game_pgn.headers['White']:
        return "white"
    return "black"

def get_user_result(game_pgn, color_played):
    result = game_pgn.headers['Result']
    score1 = result.split('-')[0]
    if score1 == "1/2":
        return "draw"
    elif score1 == '1':
        if color_played == "white":
            return "win"
        else:
            return "loss"
    else:
        if color_played == "black":
            return "win"
        else:
            return "loss"
        
def get_game_date(game_pgn):
    return game_pgn.headers['Date'].replace('.', '-')

def get_time_control(game_pgn):
    return game_pgn.headers['TimeControl']

def get_opponent_username(game_pgn, username):
    if username == game_pgn.headers['White']:
        return game_pgn.headers['Black']
    return game_pgn.headers['White']

def get_material_score(board, color_played):
    black_score = board.count('p') + board.count('n')*3 + board.count('b')*3 + board.count('r')*5 + board.count('q')*9
    white_score = board.count('P') + board.count('N')*3 + board.count('B')*3 + board.count('R')*5 + board.count('Q')*9
    if color_played == 'white':
        return white_score - black_score
    else:
        return black_score - white_score
    
def get_game_id(raw_game):
    return raw_game['uuid']

def get_rated(raw_game):
    return raw_game['rated']

def get_time_class(raw_game):
    return raw_game['time_class']

def get_user_rating(game_pgn, color_played):
    if color_played == 'white':
        return game_pgn.headers['WhiteElo']
    return game_pgn.headers['BlackElo']

def get_opponent_rating(game_pgn, color_played):
    if color_played == 'white':
        return game_pgn.headers['BlackElo']
    return game_pgn.headers['WhiteElo']

def get_total_plies(game_pgn):
    return len(list(game_pgn.mainline_moves()))


class Game:
    def __init__(self, pgn, raw_game, username):
        self.pgn = pgn
        self.player_username = username
        self.eco = get_game_eco(self.pgn)
        self.color_played = get_user_color(self.pgn, username)
        self.result = get_user_result(pgn, self.color_played)
        self.time_control = get_time_control(self.pgn)
        self.date = get_game_date(self.pgn)
        self.opponent_username = get_opponent_username(self.pgn, username)
        self.game_id = get_game_id(raw_game)
        self.rated = get_rated(raw_game)
        self.time_class = get_time_class(raw_game)
        self.user_rating = get_user_rating(pgn, self.color_played)
        self.opponent_rating = get_opponent_rating(pgn, self.color_played)
        self.total_plies = get_total_plies(self.pgn)


    def walk_through(self):
        counter = 0
        board = self.pgn.board()
        parallel_move = self.pgn.game()
        data = []
        with chess.engine.SimpleEngine.popen_uci(shutil.which("stockfish")) as engine:
            for move in self.pgn.mainline_moves():
                counter += 1
                move_turn = "white" if parallel_move.turn() else "black"
                san = board.san(move)
                parallel_move = parallel_move.next()
                timer = parallel_move.clock()
                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(depth=15))
                material_score = get_material_score(str(board), self.color_played)
                data_piece =    {'game_id': self.game_id,
                                'clock_remaining': timer,
                                'color': move_turn,
                                'material_balance': material_score,
                                'ply_number': counter,
                                'move': san,
                                'engine_eval': info["score"].white().score(mate_score=10000)
                                }
                data.append(data_piece)
        return data
    
        
    
