from axelrod_z3 import (
    ALWAYS_COOPERATE,
    ALWAYS_DEFECT,
    COOPERATE,
    DEFECT,
    GRIM_TRIGGER,
    NYDEGGER,
    RANDOM,
    STARTER_STRATEGIES,
    TIT_FOR_TAT,
    MatchConfig,
    PlayerConfig,
    best_strategies,
    is_unique_match_solution,
    payoff_table_is_prisoners_dilemma,
    solve_match,
    starter_tournament,
    strategy_round_robin,
    totals_by_strategy,
)


def test_payoff_table_has_prisoners_dilemma_ordering():
    # This checks that our payoff constants still match the Prisoner's Dilemma setup.
    assert payoff_table_is_prisoners_dilemma()


def test_forge_starter_tournament_debug_trace():
    match_one, match_two = starter_tournament(8)

    # Tit For Tat cooperates first, then copies Always Defect forever.
    assert [round_result.left_move for round_result in match_one.rounds] == [COOPERATE, DEFECT, DEFECT, DEFECT, DEFECT, DEFECT, DEFECT, DEFECT]
    assert [round_result.right_move for round_result in match_one.rounds] == [DEFECT] * 8
    assert match_one.left_total == 7
    assert match_one.right_total == 12

    # Always Cooperate and Grim Trigger both keep cooperating in this matchup.
    assert [round_result.left_move for round_result in match_two.rounds] == [COOPERATE] * 8
    assert [round_result.right_move for round_result in match_two.rounds] == [COOPERATE] * 8
    assert match_two.left_total == 24
    assert match_two.right_total == 24


def test_strategy_behavior_is_deterministic():
    # makes sure the strategy rules do not leave the solver with multiple possible traces
    assert is_unique_match_solution(
        MatchConfig(
            name="TFT_vs_AD",
            left=PlayerConfig("left", TIT_FOR_TAT),
            right=PlayerConfig("right", ALWAYS_DEFECT),
            rounds=8,
        )
    )


def test_grim_trigger_defects_after_first_opponent_defection():
    # checks the main point of Grim Trigger where it cooperates first but 
    # once the opponent defects, it never forgives.
    result = solve_match(
        MatchConfig(
            name="AD_vs_Grim",
            left=PlayerConfig("left", ALWAYS_DEFECT),
            right=PlayerConfig("right", GRIM_TRIGGER),
            rounds=5,
        )
    )

    assert [round_result.right_move for round_result in result.rounds] == [COOPERATE, DEFECT, DEFECT, DEFECT, DEFECT]


def test_random_self_match_uses_two_different_patterns():
    # checks that Random vs Random is not accidentally using the same moves for both players
    result = solve_match(
        MatchConfig(
            name="Random_vs_Random",
            left=PlayerConfig("Random", RANDOM),
            right=PlayerConfig("Random", RANDOM),
            rounds=8,
        ),
        random_seed=1710,
    )

    left_moves = [round_result.left_move for round_result in result.rounds]
    right_moves = [round_result.right_move for round_result in result.rounds]

    assert left_moves != right_moves


def test_different_random_seeds_change_random_behavior():
    # checks that Random can actually change when we choose a different seed
    config = MatchConfig(
        name="Random_vs_Random",
        left=PlayerConfig("Random", RANDOM),
        right=PlayerConfig("Random", RANDOM),
        rounds=8,
    )

    first_result = solve_match(config, random_seed=1)
    second_result = solve_match(config, random_seed=2)
    first_moves = [(round_result.left_move, round_result.right_move) for round_result in first_result.rounds]
    second_moves = [(round_result.left_move, round_result.right_move) for round_result in second_result.rounds]

    assert first_moves != second_moves


def test_random_moves_are_always_legal_for_many_seeds():
    # checks Random behavior
    config = MatchConfig(
        name="Random_vs_Random",
        left=PlayerConfig("Random", RANDOM),
        right=PlayerConfig("Random", RANDOM),
        rounds=8,
    )

    for random_seed in range(10):
        result = solve_match(config, random_seed=random_seed)
        for round_result in result.rounds:
            assert round_result.left_move in [COOPERATE, DEFECT]
            assert round_result.right_move in [COOPERATE, DEFECT]
        assert 0 <= result.left_total <= 40
        assert 0 <= result.right_total <= 40


def test_round_robin_scores_show_best_strategy_for_current_scope():
    # checks leaderboard shape 
    results = strategy_round_robin(8, random_seed=1710)
    totals = totals_by_strategy(results)
    expected_match_count = len(STARTER_STRATEGIES) * (len(STARTER_STRATEGIES) + 1) // 2

    assert len(results) == expected_match_count
    assert set(totals) == set(STARTER_STRATEGIES)
    for total in totals.values():
        assert 0 <= total <= 5 * 8 * (len(STARTER_STRATEGIES) + 1)

    best = best_strategies(results)
    assert best
    assert all(score == max(totals.values()) for _strategy, score in best)
