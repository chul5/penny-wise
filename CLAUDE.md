# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A console expense tracker (`budget_app`) built as a training assignment. **`docs/mission.md` is the
spec** — it fixes the required commands, CLI flags, output wording, and constraints. **`docs/plan.md`
is the build order**: section 9 has a numbered Done / To-do list, and section 0 records the decisions
the mission required us to pick and freeze. Read both before changing anything; a "cleaner" design
that violates the mission is wrong.

## Commands

Always use `python3.12` explicitly. Bare `python3` currently resolves to Homebrew 3.12 via PATH, but
`/usr/bin/python3` is macOS 3.9.6, where `dataclass(slots=True)` fails immediately.

```bash
python3.12 -m budget_app --help                       # all subcommands
python3.12 -m budget_app --data-dir ./data <command>  # data dir is overridable everywhere
```

There is **no test suite yet** (planned as step 29). Verification is done with throwaway snippets
against a temp directory, so a check never touches `./data`:

```bash
python3.12 - <<'PY'
import tempfile
from pathlib import Path
from budget_app.repositories import open_stores
with tempfile.TemporaryDirectory() as d:
    stores = open_stores(Path(d) / "data")
    ...
PY
```

When adding tests, they go in `tests/` and run with `python3.12 -m unittest discover -s tests`.

## Hard constraints from the mission

- **Standard library only.** No pip installs, ever. This is graded.
- **No stacktraces reach the user.** Errors print `[오류] cause` + `[힌트] fix`. Exit 0 on success,
  non-zero on failure (argparse usage errors keep its own 2).
- **All user-facing strings are Korean**, matching mission section 8's expected output. Code comments
  and docstrings are Korean too. Commit messages are English.
- **Long options only** (`--limit`, `--from`), no short flags.
- Storage is **JSONL split across three files** under the data dir: `transactions.jsonl`,
  `categories.jsonl`, `budgets.jsonl`.

## Architecture

Four layers, dependencies flowing one way only:

```
cli.py  ->  services.py  ->  repositories.py  ->  models.py
```

`repositories` never imports `services`; `models` imports nothing but `errors`. `services.py` does
not exist yet — until it does, wire handlers straight to repositories and split later.

### Storage layer (`repositories.py`) — where the real design lives

Module-level **functions** own the file mechanics; thin **classes** exist only to pin down types.
An earlier `JsonlRepository[T]` generic base with an injected loader was deliberately removed for
being over-built (see plan.md 3.4). Don't reintroduce it.

- `read_jsonl` / `read_jsonl_reversed` — both are generators. Nothing loads a whole file.
  The reverse reader `seek`s backwards in 64KB chunks so `list --limit 3` over 10,000 records
  touches ~7% of the file. This streaming is a graded requirement, not an optimization.
- `write_jsonl` — writes a temp file in the **same directory**, `fsync`s, then `os.replace`.
  There is no DB to roll back a partial write. `update`, `delete`, and category replacement all
  reuse this through `replace_all()`.
- Corrupted lines are **skipped with a warning to stderr**, never fatal. One broken line must not
  make the rest of the data unreadable. Warnings go to stderr so redirected output stays clean.
- `open_stores(data_dir) -> Stores` bundles the three stores. It does **not** create files —
  writes create them lazily, and reads treat a missing file as empty.

### Adding a command

Every handler is `(args: Namespace, stores: Stores) -> int`, registered in one line:

```python
HANDLERS["delete"] = handle_delete
```

That uniform signature is the point — it is what lets `@handle_errors` wrap all handlers identically.
`dispatch()` is a table lookup with no per-command branching.

### Validation

`validators.py` holds **pure functions only — it must never call `input()`**. That contract is what
lets interactive `add`, option-based `update`, and CSV `import` share one implementation. The
interactive re-prompt loop lives in `cli.py` as `prompt(label, parse)` for the same reason.

Validators normalize as well as check: `2024-1-5` becomes `2024-01-05`, `EXPENSE` becomes `expense`,
`15,000` becomes `15000`. Normalization matters because month filtering compares date strings
(`date[:7]`), so an unnormalized date silently breaks `summary`.

### Errors

Each `BudgetAppError` subclass in `errors.py` carries its own `hint` and `exit_code`, so the message
format is built in exactly one place instead of at every raise site. Re-raise with `from None` when
wrapping a stdlib exception, to keep the chain out of any traceback.

## Frozen decisions (do not silently change)

Recorded in plan.md section 0 because the mission demanded a choice:

- JSONL, not CSV, for storage (CSV is import/export only)
- `update` is **option-based** (`update --id X --amount N`), not interactive
- An empty category file **auto-seeds defaults** rather than blocking `add`
- `list` shows **insertion order reversed**, not date order. Back-dating an entry puts it on top.
  Strict date order would need `heapq.nlargest` and a full file read — rejected on purpose.
- Deleting the newest transaction **reuses its id**. Remaining ids stay unique; a monotonic counter
  was judged not worth a fourth file.

## Working style in this repo

**Small chunks.** Deliver one logical unit per change (~40-80 lines, one or two verification
commands), then stop for review and commit. Do not batch several files into one delivery — there is
too much to verify at once and the review stalls.

**Less code wins.** Write the simplest thing that works. Add an abstraction only once a second real
caller exists, and delete one that stopped earning its keep — a `Generic[T]` repository base and a
loader-injection layer were both removed for this reason, and the replacement was shorter *and* more
precisely typed. A plain function beats a class that only wraps one; a public attribute beats a
`@property` that just returns it. Keep docstrings to a line or two.

**Explain in English with Korean alongside.** Lead in English, then give the Korean for prose that
explains *why* — design rationale, trade-offs, caveats — marked with a leading `/`. Headings, tables,
check results, and commit messages stay English only. (Same rule as the user-level `~/.claude/CLAUDE.md`;
repeated here so this repo's convention does not depend on that file.)
