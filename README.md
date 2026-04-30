# Axelrod_Tournament

## Files

- `axelrod_z3.py`: core Z3 model, strategy constraints, payoff expressions, and scoring helpers.
- `run_debug.py`: 8-round version matching the old Forge debug run.
- `run_full.py`: 200-round version matching the old Forge full run.
- `test_axelrod_z3.py`: tests that check for payoff ordering, strategy behavior, determinism, and leaderboard output.

## How to run

From this folder:

python3 run_debug.py
python3 run_full.py
python3 -m pytest



The current model looks just at four strategies for now: `AlwaysCooperate`, `AlwaysDefect`, `TitForTat`, and `GrimTrigger`. The full output totals strategy scores so the model can directly compare which strategy performs best under the current scope.
