from .ingest import chess_data, user

def main() -> None:
    print(chess_data.get_user_game_history("ditaveve", 10))

if __name__ == "__main__":
    main()

'''
games table schema:

game id (use uuid), date, time class, whether it was rated, 
the tracked user's color, their own rating, opponent's username and rating, 
result from the tracked user's own perspective, ECO code, and total ply count

'''

'''
moves table schema:

game_id
ply_number
move
color
clock_remaining
material_balance
'''