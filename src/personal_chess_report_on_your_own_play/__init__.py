from .ingest import chess_data, user

def main() -> None:
    print(chess_data.get_user_profile("diana"))

if __name__ == "__main__":
    main()