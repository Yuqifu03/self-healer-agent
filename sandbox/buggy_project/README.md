# Buggy Project (Demo Target)

This is the demo target used to showcase AutofixAgent's self-healing loop.

## Injected defect

`main.py` imports `compute_total` from `utils.calculator`, but the module only
defines `calculate_total`. Running `python main.py` therefore fails with:

```text
ImportError: cannot import name 'compute_total' from 'utils.calculator'
```

## Expected self-healing flow

1. **Diagnose**: run `main.py` and read the traceback.
2. **Locate**: find the mismatch in `main.py` / `utils/calculator.py`.
3. **Propose**: rename the import (or the function) so they match.
4. **Fix**: apply a minimal literal patch. The cleanest single edit is renaming
   the function definition in `utils/calculator.py` from `calculate_total` to
   `compute_total` (it fixes both the import and the call site at once);
   alternatively, rename both occurrences in `main.py`.
5. **Validate**: re-run `main.py` and confirm clean `STDOUT`.

To try it locally:

```bash
PROJECT_ROOT=./sandbox/buggy_project python main.py
```

Or point `PROJECT_ROOT` at this directory in `.env` and run the agent.
