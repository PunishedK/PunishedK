# GitHub Profile Sync

Scheduled every six hours, the existing contribution snake and new GitHub activity
panel are refreshed from actual GitHub data. This workflow does not add synthetic
commits, contributions, or timestamps.

## What is counted
- Contributions, commits and created pull requests reported by the GitHub GraphQL
  `contributionsCollection` for the previous 12 months, within the workflow
  token's visibility.
- Current public repository count from GitHub REST API.
- Private activity is not automatically available to the workflow token. Turn on
  **Private contributions** under GitHub profile Contribution settings if you
  want GitHub's own contribution graph to show aggregate private activity.

The Python scripts use only Python's standard library. An API failure fails the
workflow rather than fabricating zeros. The profile stats section is inserted
only after a successful API request. SVG output is deterministic: unchanged
values do not produce new commits. Commits made by `github-actions[bot]` do not
count as your personal contributions.

## Manual refresh
GitHub > PunishedK/PunishedK > Actions > Profile Sync > Run workflow.

## Tests
```bash
python3 -m unittest discover -s tests -p 'test_profile_stats.py' -v
```
