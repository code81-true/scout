# ARCHITECTURE.md — How Scout Is Built

This document describes the physical shape of Scout:
the machines, the code, the data, the wires between
them. It is the map. When something breaks, start here.

For *why* any of this exists in this form, see SOUL.md.
This document answers *what* and *where*. It does not
argue for itself.

## Stack

- **Language:** Python 3.12+
- **Web framework:** Flask
- **WSGI server:** Gunicorn
- **Reverse proxy:** nginx
- **Database:** SQLite
- **Scheduler:** APScheduler (in-process)
- **Model provider:** Anthropic API
- **Host:** Hetzner VPS
  - IP: `178.104.57.52`
  - OS: Ubuntu 24.04
- **Source control:** GitHub

No container runtime. No Kubernetes. No Redis. No message
broker. The stack is deliberately small. Every added
component is a component that can fail at 2am.

## Domains

- `scout.regtool.org` — Scout (the interview engine)
- `compass.regtool.org` — MyTrueNorth (the daily layer)

Both served from the same VPS via nginx, terminated with
TLS. Separate application processes, separate systemd
units, separate logs.

## Session lifecycle

A Scout session moves through exactly four states, in
order. No state is skipped. No state is revisited.

```
interviewing  →  closing  →  generating  →  delivered
```

**interviewing** — The person is in the session. Scout
is asking, they are answering. The transcript grows in
memory and is persisted to SQLite after each turn.

**closing** — The interview is complete. Scout has
returned the person to the gross plane and said what it
needs to say. A 90-second timer begins. The person can
read, breathe, leave the tab open. The timer is
controlled by APScheduler.

**generating** — The closing timeout has fired. Scout
now produces the YAML spine, then the portrait, then the
five-line Meridian (constitution). This runs server-side
without the person waiting in the tab.

**delivered** — The artifacts are on disk, the recipient
has been notified, the key has been burned. The session
is finished. It does not reopen.

A session never moves backwards. If anything fails
mid-state, it fails loudly and the person is told (see
SOUL.md §6).

## Model allocation

Different stages use different models. This is cost and
latency shaped by what each model is good at.

| Stage              | Model                    | Why |
|--------------------|--------------------------|-----|
| Interview turns    | `claude-sonnet-4-5`       | Fast, calibrated, cheap enough for a two-hour context window |
| YAML extraction    | `claude-sonnet-4-5`       | Structural work — does not need Opus |
| Portrait           | `claude-opus-4-*`         | The portrait is the artifact. It gets the best model. |
| Test mode          | `claude-haiku-4-5`        | Fast and cheap — no real session, no real artifact |

Model IDs are centralised and not hardcoded at call
sites. Upgrading a model is a single-line change.

## Key system

Access to Scout is gated by single-use keys.

**Location:** `access/keys.txt` on the VPS only. Never
committed to git. Never exported. Never printed in logs.

**Format:** One key per line.
```
KEY:status:recipient
```

- `KEY` — the token the person types in
- `status` — `unused`, `active`, `used`
- `recipient` — the address the artifacts are sent to

**Lifecycle:**
1. Key generated and added to `keys.txt` as `unused`
2. Person enters key — status becomes `active`, session
   is bound to the key
3. Delivery succeeds — status becomes `used`
4. Used keys cannot be reused. Ever.

A key is a one-way door. Scout is a one-way product.

## Database

**Engine:** SQLite
**Location:** `sessions/scout.db` on the VPS

**Tables:**

- `sessions` — one row per session. Holds session id, key,
  state, timestamps, recipient, outcome flags.
- `transcripts` — one row per turn. Holds session id, role
  (scout/person), content, timestamp.

SQLite is correct here. Scout is a single-node
application with modest write volume and no concurrent
writers beyond one session at a time per key. Postgres
would be over-engineering.

The database holds the session *in flight*. Once the
session is `delivered`, the artifacts on disk are the
durable record.

## File storage

All session artifacts live on the VPS filesystem under:

```
/home/scout/spines/
```

Per session, three files are produced:

- `<session>.yaml` — the spine. Structured data.
- `<session>_portrait.txt` — the portrait. Continuous prose.
- `<session>_constitution.txt` — the Meridian. Five lines.

Files are not served from a web route by default. They
are delivered to the recipient, then retained on the VPS
only as long as operational need requires.

Custody — as stated in SOUL.md — belongs to the person.
The VPS copy is transient.

## Background scheduler

**Library:** APScheduler, running in the Flask process.

**Primary job:** closing timeout.
When a session enters the `closing` state, a job is
scheduled 90 seconds out. When it fires, the session
transitions to `generating` and the artifact pipeline
runs.

APScheduler is in-process. If the process restarts
mid-closing, the job is lost. This is a known limitation
and is acceptable given session volume. If volume grows,
move the scheduler out of process.

## Deployment pipeline

One direction only:

```
Local  →  GitHub  →  VPS (via deploy.sh)
```

- Code is written locally, committed, and pushed to
  GitHub from the local machine.
- On the VPS, `deploy.sh` pulls from GitHub, installs
  dependencies if needed, and restarts the systemd unit.
- `deploy.sh` runs **only on the VPS.** It is not run
  from the developer's machine.
- No CI/CD auto-deploys. Every production deploy is
  human-initiated and follows the PRE-DEPLOY CHECKLIST
  in `CLAUDE.md`.

Maintenance mode is toggled via `.env` on the VPS
before and after every deploy that touches user-facing
code. The checklist is mandatory.

## Scout → MTN bridge

Scout produces the spine YAML. MyTrueNorth reads it.

Today the bridge is **manual.** The YAML file is copied
by hand from Scout's output to MTN's input. There is no
API between the two systems, no shared bucket, no
automatic handoff.

This is deliberate for now. Custody matters more than
convenience. When an automatic bridge is built, it will
be designed so the person remains in control of whether
their spine moves from one system to the other.

## What this document does not cover

- The Scout system prompt — see `scout/prompt.py` and
  the review gate in `CLAUDE.md`
- The YAML schema — see the schema review gate in
  `CLAUDE.md`
- Day-to-day operational runbook — see `STATUS.md` and
  the pre-deploy checklist
- Why any of the above is shaped the way it is — see
  `SOUL.md`
