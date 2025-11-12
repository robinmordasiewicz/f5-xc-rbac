# f5-xc-user-group-sync Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-04

## Active Technologies

- Python 3.12 + requests, click, pydantic, python-dotenv, tenacity (001-xc-group-sync-plan)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
cd src
pytest
ruff check .
```

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes

- 001-precommit-requirements: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 001-xc-group-sync-plan: Added Python 3.12 + requests, click, pydantic, python-dotenv, tenacity

<!-- MANUAL ADDITIONS START -->

## CLI / Terminal safety notes (for humans and automated agents)

Root cause and symptom

- Using heredoc forms (for example: `python - <<'PY'`, `cat <<'BODY'`) or passing stdin to a CLI (for example `--body-file -`) keeps the shell's stdin open while the command runs. If the invoked CLI blocks (network, auth) or the IDE/agent runs the command without a full interactive TTY, VS Code's integrated PTY can mark the terminal as stalled and restart it with the message:

  "Restarting the terminal because the connection to the shell process was lost..."

- In short: heredoc + network/blocking operations are fragile in the integrated terminal and are a common root cause of the observed PTY restarts.

Root cause summary

- The integrated PTY in VS Code expects short-lived foreground commands. Commands that open and hold stdin (heredocs) and then perform network I/O may block the PTY event loop. When the terminal host determines the session is stalled, it forcefully restarts the PTY. This is reproducible with constructs such as `python - <<'PY'` when the invoked process performs network or blocking operations.

Strict prohibition

- Do NOT use heredoc forms (for example `<<'BODY'`, `<<'PY'`) or `--body-file -` with `gh` or other networked CLIs in the VS Code integrated terminal. These have repeatedly caused PTY restarts for users and automated agents.

Safe alternatives (copy-paste ready)

1. Portable: create a temporary file with a single shell command (printf)

```bash
printf '%s\n\n%s\n' "Short summary" "Multi-line body line 1
line 2 with `backticks` and $variables" > /tmp/issue-body.txt

gh issue create --repo owner/repo --title "Title" --body-file /tmp/issue-body.txt
rm /tmp/issue-body.txt
```

1. Safe Python one-liner (no heredoc)

```bash
python -c "open('/tmp/issue-body.txt','w',encoding='utf-8').write('Full multi-line body\nline 2 with `backticks` and $variables\n')"

gh issue create --repo owner/repo --title "Title" --body-file /tmp/issue-body.txt
rm /tmp/issue-body.txt
```

1. Embedding prepared payloads (automation)

```bash
echo 'BASE64_PAYLOAD' | base64 --decode > /tmp/issue-body.txt
gh issue create --repo owner/repo --title "Title" --body-file /tmp/issue-body.txt
rm /tmp/issue-body.txt
```

1. Prefer non-interactive API usage for automation

- Use `gh api` or `curl` with a JSON file for fully non-interactive automation (preferred for scripts and CI).

VS Code tip

- If you must run an inherently interactive or long-running command, use an external terminal. The external terminal provides a full TTY and avoids the integrated PTY restart behaviour.

## Agent conventions (for maintainers and Copilot-like agents)

- Policy: Agents MUST NEVER run heredoc forms (for example `<<'BODY'` or `<<'PY'`) or `--body-file -` in the VS Code integrated terminal for multi-line `gh` CLI bodies or other networked CLI workloads.
- Agents MUST write multi-line bodies to a temporary file non-interactively (printf/python -c/base64) and then call `gh --body-file <path>` or `gh api` with a JSON file.
- Agents SHOULD implement up to 2 retries for transient network errors when calling GitHub from an interactive terminal and must NOT keep stdin open between retries.
- When proposing commands to humans, show the file-based, non-interactive pattern as the canonical example and include a short explanation why heredoc was avoided.
- For automation (CI or scripts), prefer `gh api` or the REST API with an explicit JSON body file rather than interactive CLI flows.

<!-- MANUAL ADDITIONS END -->
