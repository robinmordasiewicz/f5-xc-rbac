#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("commit_msg_check: missing commit message file path", file=sys.stderr)
        return 1
    msg_path = Path(sys.argv[1])
    try:
        text = msg_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:  # pragma: no cover - hook path failure
        print(f"commit_msg_check: cannot read commit message: {e}", file=sys.stderr)
        return 1

    first_line = text.splitlines()[0] if text.splitlines() else ""

    # Accept if any of the following holds:
    # - Subject starts with [N]
    # - Body or subject contains 'Refs #N' / 'Closes #N' / 'Fixes #N' (case-insensitive)
    # - Fallback: any '#N' appearance
    bracket_ok = re.search(r"^\s*\[\d+\]", first_line) is not None
    verb_ok = re.search(r"(?i)\b(?:refs|closes|fixes)\s+#\d+\b", text) is not None
    hash_ok = re.search(r"#\d+", text) is not None

    if bracket_ok or verb_ok or hash_ok:
        return 0

    print(
        "Commit message must reference an issue number.\n"
        "Examples:\n"
        "  [123] Add retry/backoff\n"
        "  Refactor CSV validation (Refs #123)\n"
        "  Closes #123: enforce branch naming policy\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
