# Issue Labels: How to Verify and Create

Before creating any GitHub issue, you MUST ensure the required label(s) already exist. If a needed label is missing, create it first, then create the issue with that label.

## Verify existing labels

```sh
# List all labels (names only)
gh label list --limit 200 --json name | jq -r '.[].name'

# Check for a specific label (replace <label>)
if gh label list --limit 200 --json name | jq -r '.[].name' | grep -Fxq "<label>"; then
  echo "Label exists: <label>"
else
  echo "Label MISSING: <label>"
fi
```

## Create a label (if missing)

```sh
# Create with default color and optional description
gh label create "<label>" \
  --color 0E8A16 \
  --description "<short description>"
```

Recommended baseline labels:

- bug (#d73a4a)
- enhancement (#a2eeef)
- documentation (#0075ca)
- chore (#cfd3d7)
- test (#e4e669)
- refactor (#0366d6)

Tip: Reuse existing labels whenever possible to keep search and triage consistent.
