# Starting this project with Spec Kit + Claude Code

## 1. One-time setup (run in your terminal, not inside Claude Code)

```bash
# Install the Specify CLI (persistent install, recommended)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Create the project directory and initialize it for Claude Code
mkdir todo-agent && cd todo-agent
specify init --here --ai claude
```

If `--ai claude` is rejected by the version you install, try `--integration claude` instead — the flag name has changed between releases. Run `specify init --help` to check which your installed version expects.

This creates `.specify/` (memory, templates, scripts) and a `.claude/commands/` directory with the `/speckit.*` slash commands wired up. From here on, everything happens **inside Claude Code**, launched in this directory (`claude`).

## 2. The four files in this folder

Paste each one's content as the argument to its matching slash command, in this order. Do not skip `/speckit.constitution` — it's what keeps every later phase consistent with your actual priorities (local-first, simplicity) instead of Claude Code defaulting to whatever's conventional.

| Step | Command | File to paste in |
|---|---|---|
| 1 | `/speckit.constitution` | `01-constitution-input.md` |
| 2 | `/speckit.specify` | `02-spec-input.md` |
| 3 | `/speckit.plan` | `03-plan-input.md` |
| 4 | `/speckit.tasks` | *(no input needed — reads the plan)* |
| 5 | `/speckit.implement` | *(no input needed — executes the tasks)* |

Optional but worth doing between steps 2 and 3: run `/speckit.clarify` first. It scans the generated spec for ambiguity and asks you targeted questions before planning starts — given how many small decisions we made in this conversation (auto-calc percentage, null vs 0, etc.), it may still surface a few more.

## 3. What to expect

- `/speckit.specify` will generate `specs/001-todo-agent/spec.md` from your input — read it before moving on; it's your chance to catch a misunderstanding before code exists.
- `/speckit.plan` will generate `plan.md` (and possibly `data-model.md`, `research.md`) in the same folder — this is where the tech stack from `03-plan-input.md` gets locked in.
- `/speckit.tasks` produces `tasks.md`, a dependency-ordered checklist.
- `/speckit.implement` executes it. For a project this size, expect it to run in one sitting but check in after the CLI + `core.py` are done, before it moves to the GUI — easier to correct course early than after everything's built.

## 4. Scope reminder for this pass

v1 = CLI (free-text, Claude-parsed) + local GUI (interactive, live-updating), fully local, no scheduler, no SMS. That's deliberately encoded in the spec and constitution files below — don't let `/speckit.plan` or `/speckit.implement` wander into building the scheduler or Twilio integration this round.
