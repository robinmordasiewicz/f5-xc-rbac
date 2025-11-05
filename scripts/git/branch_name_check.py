#!/usr/bin/env python3
import re
import subprocess
import sys


def current_branch() -> str:
    try:
        out = subprocess.check_output(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except subprocess.CalledProcessError:
        return "HEAD"  # detached


def main() -> int:
    branch = current_branch()
    # Allow detached HEAD and depend on other hooks to guard merges
    if branch in ("HEAD", ""):  # pragma: no cover - rare locally
        return 0

    # main is already protected by no-commit-to-branch
    if branch == "main":
        return 0

    pattern = re.compile(r"^[0-9]+-[a-z0-9-]+$")
    if pattern.fullmatch(branch):
        return 0

    print(
        f"Branch '{branch}' does not match required pattern '^[0-9]+-[a-z0-9-]+$'\n"
        "Create a branch named with the GitHub issue number, e.g.:\n"
        "  123-fix-login-timeout\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
