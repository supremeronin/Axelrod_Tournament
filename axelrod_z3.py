from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import random

from z3 import And, If, Int, ModelRef, Or, Solver, Sum, sat


# how we store the two possible moves
COOPERATE = 0
DEFECT = 1

# the normal Prisoner's Dilemma payoff values from Axelrod tournament
# T is temptation, R is reward, P is punishment, and S is sucker's payoff.
TEMPTATION = 5
REWARD = 3
PUNISHMENT = 1
SUCKER = 0

# strategy names
ALWAYS_COOPERATE = "AlwaysCooperate"
ALWAYS_DEFECT = "AlwaysDefect"
TIT_FOR_TAT = "TitForTat"
GRIM_TRIGGER = "GrimTrigger"
NYDEGGER = "Nydegger"
RANDOM = "Random"

# starting set of strategies
STARTER_STRATEGIES = (
    ALWAYS_COOPERATE,
    ALWAYS_DEFECT,
    TIT_FOR_TAT,
    GRIM_TRIGGER,
    NYDEGGER,
    RANDOM
)


# stores a player name and the strategy that player is using
@dataclass(frozen=True)
class PlayerConfig:
    name: str
    strategy: str


# A match has a left player, a right player, and a number of rounds
@dataclass(frozen=True)
class MatchConfig:
    name: str
    left: PlayerConfig
    right: PlayerConfig
    rounds: int


# stores what happened in one round after Z3 solves the match
@dataclass(frozen=True)
class RoundResult:
    round_number: int
    left_move: int
    right_move: int
    left_score: int
    right_score: int


# stores the full solved match including every round and the total scores
@dataclass(frozen=True)
class MatchResult:
    config: MatchConfig
    rounds: tuple[RoundResult, ...]
    left_total: int
    right_total: int


def legal_action(action):
    # every move has to be either cooperate or defect.
    return Or(action == COOPERATE, action == DEFECT)


def payoff_to_first(left_move, right_move):
    # score for the left player in one round
    return If(
        And(left_move == COOPERATE, right_move == COOPERATE),
        REWARD,
        If(
            And(left_move == COOPERATE, right_move == DEFECT),
            SUCKER,
            If(And(left_move == DEFECT, right_move == COOPERATE), TEMPTATION, PUNISHMENT),
        ),
    )


def payoff_to_second(left_move, right_move):
    # same payoff table but from the right player's point of view
    # only difference is who gets temptation and who gets sucker's payoff
    return If(
        And(left_move == COOPERATE, right_move == COOPERATE),
        REWARD,
        If(
            And(left_move == COOPERATE, right_move == DEFECT),
            TEMPTATION,
            If(And(left_move == DEFECT, right_move == COOPERATE), SUCKER, PUNISHMENT),
        ),
    )


def strategy_constraints(strategy: str, own_moves, opponent_moves):
    # returns rules that force a player's moves to match their strategy
    if strategy == ALWAYS_COOPERATE:
        return [move == COOPERATE for move in own_moves]

    if strategy == ALWAYS_DEFECT:
        return [move == DEFECT for move in own_moves]

    if strategy == TIT_FOR_TAT:
        # Tit For Tat starts by cooperating and after that it
        # copies what the opponent did in the last round.
        constraints = [own_moves[0] == COOPERATE]
        constraints.extend(own_moves[round_index] == opponent_moves[round_index - 1] for round_index in range(1, len(own_moves)))
        return constraints

    if strategy == GRIM_TRIGGER:
        # Grim Trigger starts by cooperating then if the opponent has ever 
        # defected before it defects forever after.
        constraints = [own_moves[0] == COOPERATE]
        for round_index in range(1, len(own_moves)):
            opponent_defected_before = Or(*[opponent_moves[past] == DEFECT for past in range(round_index)])
            constraints.append(own_moves[round_index] == If(opponent_defected_before, DEFECT, COOPERATE))
        return constraints
    
    if strategy == NYDEGGER:
        # Nydegger strategy:
        # - Cooperate in round 1
        # - In round 2, cooperate if opponent cooperated in round 1, else defect
        # - From round 3 onward:
        #   - If opponent ever defected in rounds 1-2, play Grim Trigger (defect forever)
        #   - Otherwise, play Tit for Tat
        constraints = [own_moves[0] == COOPERATE]
        
        if len(own_moves) > 1:
            # Round 2: mirror opponent's move from round 1
            constraints.append(own_moves[1] == opponent_moves[0])
        
        # Round 3 and beyond
        if len(own_moves) > 2:
            # Check if opponent defected in rounds 1 or 2
            opponent_defected_early = Or(opponent_moves[0] == DEFECT, opponent_moves[1] == DEFECT)
            for round_index in range(2, len(own_moves)):
                # If opponent defected in early rounds, defect forever (Grim Trigger)
                # Otherwise, play Tit for Tat (copy opponent's last move)
                constraints.append(
                    own_moves[round_index] == If(
                        opponent_defected_early,
                        DEFECT,
                        opponent_moves[round_index - 1]
                    )
                )
        
        return constraints
    
    if strategy == RANDOM:
        # RANDOM strategy: use Python's random to generate a random sequence,
        # then constrain Z3 to follow it
        constraints = []
        for move in own_moves:
            random_choice = random.choice([COOPERATE, DEFECT])
            constraints.append(move == random_choice)
        return constraints

    raise ValueError(f"unknown strategy: {strategy}")


def action_name(action: int) -> str:
    if action == COOPERATE:
        return "C"
    if action == DEFECT:
        return "D"
    raise ValueError(f"unknown action value: {action}")


def _model_int(model: ModelRef, expr) -> int:
    # this turns one solved expression into a normal Python integer 
    # that to print or test with
    value = model.evaluate(expr, model_completion=True)
    return value.as_long()


def solve_match(config: MatchConfig) -> MatchResult:
    # makes a Z3 variable for each player's move in each round,
    # adds the strategy and payoff rules, and then asks Z3 for a trace
    if config.rounds < 1:
        raise ValueError("rounds must be positive")

    solver = Solver()

    # These lists are the temporal trace.
    # So for example, left_moves[0] is the left player's move in round 1.
    left_moves = [Int(f"{config.name}_left_move_{round_index}") for round_index in range(config.rounds)]
    right_moves = [Int(f"{config.name}_right_move_{round_index}") for round_index in range(config.rounds)]

    # every move must be legal
    for move in left_moves + right_moves:
        solver.add(legal_action(move))

    # each player sees the other player's moves as the opponent history
    solver.add(strategy_constraints(config.left.strategy, left_moves, right_moves))
    solver.add(strategy_constraints(config.right.strategy, right_moves, left_moves))

    # symbolic score expressions for each round
    left_scores = [payoff_to_first(left_moves[i], right_moves[i]) for i in range(config.rounds)]
    right_scores = [payoff_to_second(left_moves[i], right_moves[i]) for i in range(config.rounds)]

    # ff satisfiable, Z3 found a legal set of moves
    result = solver.check()
    if result != sat:
        raise RuntimeError(f"match constraints were not satisfiable: {result}")

    model = solver.model()
    round_results = []
    for round_index in range(config.rounds):
        round_results.append(
            RoundResult(
                round_number=round_index + 1,
                left_move=_model_int(model, left_moves[round_index]),
                right_move=_model_int(model, right_moves[round_index]),
                left_score=_model_int(model, left_scores[round_index]),
                right_score=_model_int(model, right_scores[round_index]),
            )
        )

    return MatchResult(
        config=config,
        rounds=tuple(round_results),
        left_total=_model_int(model, Sum(left_scores)),
        right_total=_model_int(model, Sum(right_scores)),
    )


def starter_tournament(rounds: int) -> tuple[MatchResult, ...]:
    return (
        solve_match(
            MatchConfig(
                name="MatchOne",
                left=PlayerConfig("TFTPlayer", TIT_FOR_TAT),
                right=PlayerConfig("ADPlayer", ALWAYS_DEFECT),
                rounds=rounds,
            )
        ),
        solve_match(
            MatchConfig(
                name="MatchTwo",
                left=PlayerConfig("ACPlayer", ALWAYS_COOPERATE),
                right=PlayerConfig("GrimPlayer", GRIM_TRIGGER),
                rounds=rounds,
            )
        ),
    )


def strategy_round_robin(rounds: int, strategies: Iterable[str] = STARTER_STRATEGIES) -> tuple[MatchResult, ...]:
    # runs every pair of strategies against each other one time
    strategies = tuple(strategies)
    matches = []
    for left_index, left_strategy in enumerate(strategies):
        for right_index, right_strategy in enumerate(strategies):
            if left_index > right_index:
                continue
            matches.append(
                solve_match(
                    MatchConfig(
                        name=f"{left_strategy}_vs_{right_strategy}",
                        left=PlayerConfig(left_strategy, left_strategy),
                        right=PlayerConfig(right_strategy, right_strategy),
                        rounds=rounds,
                    )
                )
            )
    return tuple(matches)


def totals_by_strategy(matches: Iterable[MatchResult]) -> dict[str, int]:
    # adds up all the scores for each strategy across all matches
    totals: dict[str, int] = {}
    for match in matches:
        totals[match.config.left.strategy] = totals.get(match.config.left.strategy, 0) + match.left_total
        totals[match.config.right.strategy] = totals.get(match.config.right.strategy, 0) + match.right_total
    return totals


def best_strategies(matches: Iterable[MatchResult]) -> list[tuple[str, int]]:
    # finds the strategy or strategies with the highest total score
    totals = totals_by_strategy(matches)
    if not totals:
        return []
    best_score = max(totals.values())
    return sorted((strategy, score) for strategy, score in totals.items() if score == best_score)


def format_match(result: MatchResult, show_rounds: bool = True) -> str:
    left = result.config.left
    right = result.config.right
    lines = [
        f"{result.config.name}: {left.name} ({left.strategy}) vs {right.name} ({right.strategy})",
        f"totals: {left.name}={result.left_total}, {right.name}={result.right_total}",
    ]
    if show_rounds:
        lines.append("round | left | right | score")
        for round_result in result.rounds:
            lines.append(
                f"{round_result.round_number:>5} | "
                f"{action_name(round_result.left_move):>4} | "
                f"{action_name(round_result.right_move):>5} | "
                f"{round_result.left_score}-{round_result.right_score}"
            )
    return "\n".join(lines)


def format_leaderboard(matches: Iterable[MatchResult]) -> str:
    # convert strategy totals into a ranked leaderboard
    totals = totals_by_strategy(matches)
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    lines = ["strategy leaderboard"]
    for rank, (strategy, total) in enumerate(ordered, start=1):
        lines.append(f"{rank}. {strategy}: {total}")

    winners = best_strategies(matches)
    if winners:
        winner_text = ", ".join(strategy for strategy, _score in winners)
        lines.append(f"best strategy: {winner_text}")
    return "\n".join(lines)


def is_unique_match_solution(config: MatchConfig) -> bool:
    # checks whether the strategy rules force exactly one possible trace.
    solver = Solver()
    left_moves = [Int(f"unique_{config.name}_{config.left.name}_move_{round_index}") for round_index in range(config.rounds)]
    right_moves = [Int(f"unique_{config.name}_{config.right.name}_move_{round_index}") for round_index in range(config.rounds)]

    for move in left_moves + right_moves:
        solver.add(legal_action(move))
    solver.add(strategy_constraints(config.left.strategy, left_moves, right_moves))
    solver.add(strategy_constraints(config.right.strategy, right_moves, left_moves))

    if solver.check() != sat:
        return False
    model = solver.model()

    # save the first solution then tell the solver to find a different one and if
    # it can't find another one then the match behavior is deterministic.
    first_solution = [model.evaluate(move, model_completion=True) for move in left_moves + right_moves]
    solver.add(Or(*[move != value for move, value in zip(left_moves + right_moves, first_solution)]))
    return solver.check() != sat


def payoff_table_is_prisoners_dilemma() -> bool:
    # checks that the payoff numbers are in the right Prisoner's Dilemma order
    return TEMPTATION > REWARD > PUNISHMENT > SUCKER
