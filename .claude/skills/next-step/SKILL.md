---
name: next-step
description: Implement the next item from docs/plan.md section 9 as one small reviewable chunk. Use when the user says "next", "proceed", "proceed next", or asks for the next step of the budget_app assignment. Reads the plan, implements exactly one logical unit, verifies it against a temp data dir, reports results, and stops for review.
---

# Next plan step

Implement **one** item from the build order and stop. The user reviews and commits each chunk
personally; a delivery they cannot verify in one pass stalls the review.

## 1. Find the work

Read `docs/plan.md` section 9. It has a **Done** table and a **To do** table.

Take the lowest-numbered item in **To do**. If the user named a specific step, use that instead.

Cross-check against the code before starting — the plan can lag reality. If the item already
exists, mark it Done in the plan, say so, and move to the following item.

## 2. Split if needed

One chunk is **one logical unit inside one file**, roughly 40-80 lines, verifiable with one or two
commands. If the plan item is bigger than that, split it and do only the first part. Say what the
remaining parts are.

Example: "category add/list" splits into (a) the service function plus the validator it needs,
(b) the CLI handlers. Deliver (a), stop.

Touching a second file is acceptable only when it is a few lines directly serving the same unit
(a 6-line validator for the service being written). Never batch independent files together.

## 3. Implement

Follow `CLAUDE.md`. The rules that get broken most often:

- **Standard library only.** No pip, ever — it is graded.
- **Write the simplest thing that works.** No generics, dependency injection, or base classes
  until a second real caller exists. A plain function beats a class wrapping one function.
- **Korean** for code comments, docstrings, and every user-facing string. English commit messages.
- **Handlers never contain `try/except`** — `@handle_errors` owns that. Handler signature is
  always `(args: Namespace, stores: Stores) -> int`, registered as `HANDLERS["name"] = handler`.
- **Nothing loads a whole file.** Reads go through the generators in `repositories.py`.
- `validators.py` must never call `input()`.
- Do not reintroduce the `JsonlRepository[T]` generic base — it was deliberately removed.

## 4. Verify

Run real checks and show their output. Never claim something works without evidence.

Always use `python3.12` explicitly, and always against a temp directory so `./data` is untouched:

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

Cover, where they apply:

- the happy path
- **every error path**, with its exit code (0 success, 1 domain error, 2 file/argparse, 130 interrupt)
- edge cases: empty file, missing file, corrupted line, Korean text, duplicate input
- **regression** on what already worked — at minimum `python3.12 -m budget_app --version` and one
  storage-layer round trip
- for anything touching reads, prove streaming (compare bytes read against file size, or count
  loader calls) rather than asserting it

If a check fails, fix it in this chunk. If verification exposes a design problem, say so plainly
and explain the trade-off — a silently wrong `summary` matters more than finishing the step.

## 5. Report and stop

Report in **English with Korean alongside**: lead in English, and give the Korean for prose that
explains *why* — rationale, trade-offs, caveats — marked with a leading `/`. Headings, tables,
check results, and commit messages stay English only.

Include:

- what was added, as the actual signatures
- **why**, for any decision that could look arbitrary later
- a verification table with real results
- anything deliberately left out, and what would trigger doing it
- a suggested English commit message (`feat:`/`fix:`/`refactor:`/`docs:`, imperative mood, under
  50 chars) with a body explaining *why* when it is not obvious
- what the next step is

Then **stop**. Do not begin the next item, even if it is small.

## 6. Keep the plan honest

When an implementation diverges from `docs/plan.md`, update the plan in the same chunk and say what
changed. A plan that no longer matches the code is worse than no plan. Move finished items from
**To do** to **Done**.
