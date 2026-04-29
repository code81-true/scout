# SESSION_REPORTING.md — Scout Session Report Format
# Append a new entry after every git push, VPS deploy, or milestone.
# Referenced by CLAUDE.md.

## Session Reporting Rule

After every `git push`, deployment to VPS, or milestone completion,
append a new entry to `SESSION_REPORT.md` in the project root.
Do not wait for session end. Do not overwrite previous entries.
Newest entry goes at the top of the file. The file is a permanent
running changelog.

Format — append above all previous entries:

---

## {date, time} — {one-line summary of what just shipped}
**Trigger:** git push / deploy / milestone

### Shipped
- {what was completed and committed}

### Deployed
- {what hit VPS, or "Not yet deployed"}

### Decisions Made
- {any decisions with reasoning, or "None"}

### Blockers Resolved
- {anything unblocked, or "None"}

### New Blockers
- {anything now stuck, or "None"}

### PM Note
- {anything the project PM needs to know — timeline impact,
  scope change, dependency on MTN or commercial, risk flagged}

---

This file is read by the project PM in MTN_SCOUT_MARKET.
Never delete previous entries. The history is the audit trail.
