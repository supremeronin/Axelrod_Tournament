from axelrod_z3 import format_leaderboard, format_match, starter_tournament, strategy_round_robin
import time

ROUNDS = 200


def main() -> None:
    random_seed = time.time_ns()
    print(f"random seed: {random_seed}")
    print()

    # only prints total scores for each match
    print(f"starter tournament ({ROUNDS} rounds)")
    print()
    for match in starter_tournament(ROUNDS, random_seed=random_seed):
        print(format_match(match, show_rounds=False))
        print()

    # totals how each strategy does against the other starter strategies
    print(f"strategy round robin ({ROUNDS} rounds)")
    print()
    round_robin = strategy_round_robin(ROUNDS, random_seed=random_seed)
    for match in round_robin:
        print(format_match(match, show_rounds=False))
    print()
    print(format_leaderboard(round_robin))


if __name__ == "__main__":
    main()
