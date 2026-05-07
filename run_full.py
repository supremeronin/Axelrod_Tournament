from axelrod_z3 import format_leaderboard, format_match, starter_tournament, strategy_round_robin, totals_by_strategy
import time
import argparse

ROUNDS = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Axelrod tournaments with optional averaging.")
    parser.add_argument(
        "-t",
        "--tournaments",
        type=int,
        default=1,
        help="number of round-robin tournaments to run and average (default: 1)",
    )
    return parser.parse_args()


def print_average_leaderboard(tournament_count: int, base_seed: int) -> None:
    running_totals: dict[str, int] = {}

    for tournament_index in range(tournament_count):
        tournament_seed = base_seed + tournament_index
        round_robin = strategy_round_robin(ROUNDS, random_seed=tournament_seed)
        totals = totals_by_strategy(round_robin)
        for strategy, score in totals.items():
            running_totals[strategy] = running_totals.get(strategy, 0) + score

    averaged = sorted(
        ((strategy, total / tournament_count) for strategy, total in running_totals.items()),
        # Negative score for descending order, then by strategy name for tie-breaking in alphabetical order
        key=lambda item: (-item[1], item[0]),
    )

    print(f"strategy round robin average leaderboard ({ROUNDS} rounds, {tournament_count} tournaments)")
    print()
    for rank, (strategy, average_score) in enumerate(averaged, start=1):
        print(f"{rank}. {strategy}: {average_score:.2f}")


def main() -> None:
    args = parse_args()
    if args.tournaments < 1:
        raise ValueError("--tournaments must be at least 1")

    random_seed = time.time_ns()
    print(f"random seed: {random_seed}")
    print()

    if args.tournaments > 1:
        print_average_leaderboard(args.tournaments, random_seed)
        return

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
