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

The current model compares the starter strategies and the debug visual shows the short trace so the model is easier to explain.
