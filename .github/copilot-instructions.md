# f5-xc-rbac Development Guidelines

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
<!-- MANUAL ADDITIONS END -->

<!-- MANUAL ADDITIONS START -->

## CLI / Terminal safety notes (for humans and automated agents)

- Avoid placing backticks (`` ` ``) inside unescaped double-quoted strings in shell commands. In shells like `zsh` and `bash` backticks perform command substitution and will be executed.

- Prefer one of these safe patterns when composing multi-line CLI bodies (for example, `gh issue comment` or `gh pr create` bodies):

  - Heredoc with a quoted delimiter (recommended):

    ```bash
    gh issue comment 43 --body <<'BODY'
    Multi-line text with `backticks`, $variables, and "quotes" is safe here.
    BODY
    ```

  - Use `--body-file` or write the content to a temporary file and pass the path:

    ```bash
    cat > /tmp/body.txt <<'EOF'
    Multi-line content
    EOF
    gh issue comment 43 --body-file /tmp/body.txt
    ```

  - If an inline string is necessary, use single quotes around the body so backticks are literal:

    ```bash
    gh issue comment 43 --body 'Use `backticks` literally in this single-quoted string.'
    ```

  - If double quotes must be used, escape backticks (for example: "Make \`cmd\` literal").

- When an automated agent runs commands on your behalf (for example, using a terminal tool):

  - Always preface the command with a one-line why/what/outcome sentence describing the intent.
  - Use a quoted heredoc or `--body-file` for any multi-line argument that may contain backticks, dollar signs, or other characters that the shell would expand.
  - Never inject unescaped user-provided content into a double-quoted shell string.

## Agent conventions (for maintainers and Copilot-like agents)

- When preparing `gh` commands that include multi-line bodies, prefer heredoc (`<<'BODY'`) or `--body-file` to avoid accidental command substitution.
- If you must include small inline bodies, use single quotes to prevent expansion. If you must use double quotes, escape backticks and dollar signs.
- When calling a terminal-run tool, do not place backtick-containing text inside an unescaped double-quoted argument. Use heredoc or file instead.
- For reproducibility, prefer the `--body-file` pattern when automating or generating long issue/pr bodies.
- When showing examples in documentation, always show the safe heredoc or `--body-file` pattern as the canonical form.

<!-- MANUAL ADDITIONS END -->
