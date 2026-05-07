# Axelrod_Tournament

## Files

- `axelrod_z3.py`: core Z3 model, strategy constraints, payoff expressions, and scoring helpers.
- `run_debug.py`: 8-round version matching the old Forge debug run.
- `run_full.py`: 200-round version matching the old Forge full run.
- `visualize_debug.py`: creates an HTML visual for the 8-round debug run.
- `test_axelrod_z3.py`: tests that check for payoff ordering, strategy behavior, determinism, and leaderboard output.

## How to run

python3 run_debug.py
python3 run_full.py
python3 visualize_debug.py
python3 -m pytest



`visualize_debug.py` writes `debug_visualization.html`, which you can open in a browser.

`run_full.py` and `visualize_debug.py` show the Random seed they used and those commands choose a new seed each run so the Random strategy can change.

## Strategies
Always Cooperate: For every round, we add a constraint saying its move has to be COOPERATE.

Always Defect: Reverse of above so its move every round is DEFECT.

Tit For Tat: Starts by cooperating in first round. After that, it copies whatever the oppenent did in the previous round. So essentially, own move this round = opponent move last round

Grim Trigger: Starts by cooperating but once the opponent defects just once, Grim Trigger defects forever after that. So for each round we check whether the opponent has defected in an earlier round and if they have then Grim Trigger plays D and if not keep with C.

Random: Makes a random list of moves before the match is solved. So for each round, Python chooses either C or D, then constraints are given saying Random has to follow that exact list for that match. But for this to be different across runs, we had to use a seed which controls which random pattern gets made. If we don't pass in a seed then a new one will be made using the current time.

Nydegger: Starts with tit-for-tat for 2 rounds. If the opponent defected in the first two rounds, plays as grim trigger for the rest of the game. Else, continues to play as tit-for-tat.





## AI
For the visual, we used AI to help make a simple HTML visualization for the debug version of the model. We wanted something kind of like the Forge/Sterling visual but since we moved the model to Z3, we needed a different way to show the traces.
AI helped write visualize_debug.py, which takes the solved 8-round Z3 results and turns them into debug_visualization.html. The visual shows each matchup as a small timeline where green means cooperate and red means defect. It also shows the score for each round and a leaderboard at the bottom.
We used AI mostly for the structure and formatting of the visual, but the visual is still based on our actual model output. It does not create new results by itself; it just shows the Z3 match results in a way that is easier to understand and prettier to look at.