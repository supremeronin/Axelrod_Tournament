from axelrod_z3 import format_leaderboard, format_match, starter_tournament, strategy_round_robin


# short version of the tournament -- probably don't need this file since Z3 is 
# working perfectly for the full run
ROUNDS = 8


def main() -> None:
    print(f"starter tournament ({ROUNDS} rounds)")
    print()
    for match in starter_tournament(ROUNDS):
        print(format_match(match))
        print()

    print(f"strategy round robin ({ROUNDS} rounds)")
    print()
    round_robin = strategy_round_robin(ROUNDS)
    for match in round_robin:
        print(format_match(match, show_rounds=False))
    print()
    print(format_leaderboard(round_robin))


if __name__ == "__main__":
    main()
