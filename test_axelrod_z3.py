from axelrod_z3 import (
    ALWAYS_COOPERATE,
    ALWAYS_DEFECT,
    COOPERATE,
    DEFECT,
    GRIM_TRIGGER,
    RANDOM,
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
        )
    )

    assert [round_result.left_move for round_result in result.rounds] == [DEFECT, COOPERATE, COOPERATE, DEFECT, DEFECT, DEFECT, COOPERATE, COOPERATE]
    assert [round_result.right_move for round_result in result.rounds] == [DEFECT, COOPERATE, DEFECT, DEFECT, COOPERATE, COOPERATE, COOPERATE, COOPERATE]


def test_round_robin_scores_show_best_strategy_for_current_scope():
    # checks the leaderboard for the current small strategy set we have
    results = strategy_round_robin(8)
    totals = totals_by_strategy(results)

    assert totals[ALWAYS_DEFECT] == 100
    assert totals[TIT_FOR_TAT] == 121
    assert totals[GRIM_TRIGGER] == 118
    assert totals[ALWAYS_COOPERATE] == 111
    assert totals[RANDOM] == 105
    assert best_strategies(results) == [(TIT_FOR_TAT, 121)]
