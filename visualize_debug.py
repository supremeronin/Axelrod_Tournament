from __future__ import annotations

import time
from html import escape
from pathlib import Path

from axelrod_z3 import (
    COOPERATE,
    MatchResult,
    best_strategies,
    starter_tournament,
    strategy_round_robin,
    totals_by_strategy,
)


ROUNDS = 8
OUTPUT_FILE = Path("debug_visualization.html")


def move_text(move: int) -> str:
    # this is the label that goes inside each colored move box
    if move == COOPERATE:
        return "C"
    return "D"


def move_class(move: int) -> str:
    # Cooperate and defect get different colors in the visual
    if move == COOPERATE:
        return "cooperate"
    return "defect"


def render_player_row(player_name: str, moves: list[int]) -> str:
    # makes one row of the trace like one player across all 8 rounds
    cells = "\n".join(
        f'<div class="move {move_class(move)}">{move_text(move)}</div>'
        for move in moves
    )
    return f"""
        <div class="player-name">{escape(player_name)}</div>
        <div class="moves">{cells}</div>
    """


def render_score_row(match: MatchResult) -> str:
    # shows the score from each round underneath the moves
    scores = "\n".join(
        f'<div class="score-cell">{round_result.left_score}-{round_result.right_score}</div>'
        for round_result in match.rounds
    )
    return f"""
        <div class="player-name">score</div>
        <div class="scores">{scores}</div>
    """


def render_match(match: MatchResult) -> str:
    # turns one solved match into a timeline card
    left = match.config.left
    right = match.config.right
    left_moves = [round_result.left_move for round_result in match.rounds]
    right_moves = [round_result.right_move for round_result in match.rounds]
    round_labels = "\n".join(f'<div class="round-cell">{round_result.round_number}</div>' for round_result in match.rounds)

    return f"""
    <section class="match">
        <div class="match-title">
            <h2>{escape(match.config.name)}</h2>
            <p>{escape(left.name)} ({escape(left.strategy)}) vs {escape(right.name)} ({escape(right.strategy)})</p>
        </div>

        <div class="trace-grid">
            <div class="player-name">round</div>
            <div class="rounds">{round_labels}</div>
            {render_player_row(left.name, left_moves)}
            {render_player_row(right.name, right_moves)}
            {render_score_row(match)}
        </div>

        <div class="totals">
            <span>{escape(left.name)} total: <strong>{match.left_total}</strong></span>
            <span>{escape(right.name)} total: <strong>{match.right_total}</strong></span>
        </div>
    </section>
    """


def render_leaderboard(matches: tuple[MatchResult, ...]) -> str:
    # makes a simple bar chart from the round robin totals.
    totals = totals_by_strategy(matches)
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    max_score = max(totals.values()) if totals else 1
    winner_names = {strategy for strategy, _score in best_strategies(matches)}

    rows = []
    for rank, (strategy, total) in enumerate(ordered, start=1):
        width = round((total / max_score) * 100)
        winner_class = " winner" if strategy in winner_names else ""
        rows.append(
            f"""
            <div class="leader-row{winner_class}">
                <div class="leader-rank">{rank}</div>
                <div class="leader-name">{escape(strategy)}</div>
                <div class="bar-wrap"><div class="bar" style="width: {width}%"></div></div>
                <div class="leader-score">{total}</div>
            </div>
            """
        )

    winner_text = ", ".join(sorted(winner_names))
    return f"""
    <section class="leaderboard">
        <h2>Strategy leaderboard</h2>
        <p>Scores from the 8-round round robin.</p>
        <div class="leader-table">
            {''.join(rows)}
        </div>
        <div class="winner-text">best strategy: <strong>{escape(winner_text)}</strong></div>
    </section>
    """


def render_page(starter_matches: tuple[MatchResult, ...], round_robin: tuple[MatchResult, ...], random_seed: int) -> str:
    # puts the whole visual page together
    starter_matches_html = "\n".join(render_match(match) for match in starter_matches)
    round_robin_html = "\n".join(render_match(match) for match in round_robin)
    leaderboard_html = render_leaderboard(round_robin)
    match_count = len(round_robin)

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Axelrod Tournament Debug Visual</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f7f8fb;
            --ink: #17202a;
            --muted: #5f6b7a;
            --line: #d9dee8;
            --panel: #ffffff;
            --coop: #2d9d68;
            --defect: #c94c4c;
            --accent: #315fbd;
            --accent-light: #dfe8ff;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: var(--bg);
            color: var(--ink);
            font-family: Arial, Helvetica, sans-serif;
        }}

        main {{
            width: min(1100px, calc(100% - 32px));
            margin: 28px auto 40px;
        }}

        header {{
            margin-bottom: 22px;
        }}

        h1, h2, p {{
            margin: 0;
        }}

        h1 {{
            font-size: 30px;
            line-height: 1.15;
        }}

        h2 {{
            font-size: 20px;
            line-height: 1.25;
        }}

        p {{
            color: var(--muted);
            margin-top: 4px;
        }}

        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin-top: 14px;
            color: var(--muted);
            font-size: 14px;
        }}

        .legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .legend-box {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
        }}

        .match,
        .section-heading,
        .leaderboard {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            margin-top: 16px;
        }}

        .section-heading {{
            padding: 16px 18px;
            background: #fdfefe;
        }}

        .match-title {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: baseline;
            margin-bottom: 16px;
        }}

        .trace-grid {{
            display: grid;
            grid-template-columns: minmax(110px, 160px) 1fr;
            gap: 8px 12px;
            align-items: center;
        }}

        .player-name {{
            color: var(--muted);
            font-size: 14px;
            font-weight: 700;
            min-width: 0;
            overflow-wrap: anywhere;
        }}

        .rounds,
        .moves,
        .scores {{
            display: grid;
            grid-template-columns: repeat({ROUNDS}, minmax(34px, 1fr));
            gap: 6px;
        }}

        .round-cell,
        .score-cell,
        .move {{
            min-height: 34px;
            display: grid;
            place-items: center;
            border-radius: 6px;
            font-weight: 700;
        }}

        .round-cell,
        .score-cell {{
            background: #eef1f6;
            color: var(--muted);
            font-size: 13px;
        }}

        .move {{
            color: white;
            font-size: 15px;
        }}

        .cooperate {{
            background: var(--coop);
        }}

        .defect {{
            background: var(--defect);
        }}

        .totals {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            border-top: 1px solid var(--line);
            margin-top: 16px;
            padding-top: 12px;
            color: var(--muted);
        }}

        .leader-table {{
            display: grid;
            gap: 10px;
            margin-top: 16px;
        }}

        .leader-row {{
            display: grid;
            grid-template-columns: 32px minmax(120px, 190px) 1fr 58px;
            gap: 10px;
            align-items: center;
        }}

        .leader-rank,
        .leader-score {{
            color: var(--muted);
            font-weight: 700;
        }}

        .leader-name {{
            font-weight: 700;
            overflow-wrap: anywhere;
        }}

        .bar-wrap {{
            height: 20px;
            background: #eef1f6;
            border-radius: 5px;
            overflow: hidden;
        }}

        .bar {{
            height: 100%;
            background: var(--accent);
        }}

        .winner .leader-name {{
            color: var(--accent);
        }}

        .winner .bar-wrap {{
            background: var(--accent-light);
        }}

        .winner-text {{
            border-top: 1px solid var(--line);
            margin-top: 16px;
            padding-top: 12px;
        }}

        @media (max-width: 720px) {{
            main {{
                width: min(100% - 20px, 1100px);
                margin-top: 18px;
            }}

            .match-title {{
                display: block;
            }}

            .trace-grid {{
                grid-template-columns: 1fr;
                gap: 6px;
            }}

            .player-name {{
                margin-top: 8px;
            }}

            .leader-row {{
                grid-template-columns: 28px minmax(90px, 1fr) 52px;
            }}

            .bar-wrap {{
                grid-column: 2 / 4;
            }}
        }}
    </style>
</head>
<body>
    <main>
        <header>
            <h1>Axelrod Tournament Debug Visual</h1>
            <p>8-round Z3 debug trace with all {match_count} round-robin matches</p>
            <div class="legend">
                <span class="legend-item"><span class="legend-box cooperate"></span>Cooperate</span>
                <span class="legend-item"><span class="legend-box defect"></span>Defect</span>
                <span class="legend-item">random seed: <strong>{random_seed}</strong></span>
            </div>
        </header>

        <section class="section-heading">
            <h2>Starter tournament</h2>
            <p>The original two demo matches from the Forge version.</p>
        </section>
        {starter_matches_html}

        <section class="section-heading">
            <h2>Round robin traces</h2>
            <p>All {match_count} strategy matchups, including self matches.</p>
        </section>
        {round_robin_html}

        {leaderboard_html}
    </main>
</body>
</html>
"""


def main() -> None:
    # seed changes each time so the Random strategy changes in the visual
    random_seed = time.time_ns()
    starter_matches = starter_tournament(ROUNDS, random_seed=random_seed)
    round_robin = strategy_round_robin(ROUNDS, random_seed=random_seed)
    OUTPUT_FILE.write_text(render_page(starter_matches, round_robin, random_seed), encoding="utf-8")
    print(f"random seed: {random_seed}")
    print(f"wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
