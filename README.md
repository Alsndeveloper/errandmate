# ErrandMate

[![CI](https://github.com/Alsndeveloper/errandmate/actions/workflows/ci.yml/badge.svg)](https://github.com/Alsndeveloper/errandmate/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

A local errand marketplace: people post everyday errands (grocery runs, pharmacy
pickups, dog walks), and nearby "runners" accept and complete them. Built with a
FastAPI backend, SQLite, and a vanilla-JS single-page web app.

## Background

ErrandMate began as a group project at Cardiff Metropolitan University, built as
a Tkinter desktop prototype (kept in [`ErrandMate/`](ErrandMate/) for reference).

I later rebuilt it on my own as a web application: a REST API, a new browser UI, a
rule-based "smart assistant" layer, and an automated test suite. I used AI coding
assistants (Google Antigravity, Claude Code) during the rebuild, and I reviewed and
tested the code myself.

## Features

- **Errand lifecycle:** open → accepted → in progress → awaiting confirmation → completed (or cancelled), with permission checks at every step (for example, you can't accept your own errand).
- **Natural-language drafting:** type *"walk my dog Monday 9pm at CF24 9ZZ"* and the app pulls out the task, category, time and address with regex and keyword rules.
- **Fair-price suggestions:** a heuristic estimate based on the UK National Living Wage, effort multipliers and duration, with flags for suspiciously low or high prices.
- **Runner matching:** ranks runners by a weighted score (category experience 30%, smoothed rating 30%, proximity 20%, workload 20%) and shows *why* each one matched.
- **Completion checks:** four rule-based checks before an errand completes: plausible duration, keyword overlap with the task, no self-dealing, and a valid price.
- **Ratings and dashboard:** 1–5 star reviews (one per errand) and KPI cards.

> **About the "AI" layer:** these features are deterministic, rule-based and
> heuristic algorithms written in plain Python. They are not machine-learning
> models or LLM calls. That keeps them fast, explainable and testable.

## Architecture

```
web/ (HTML + Tailwind + vanilla JS)
   │  fetch JSON
   ▼
server/app.py ── routes/ (auth, tasks, ratings, profile, stats, ai)
   │                 │
   │                 └── ai/ (nlp_extractor, pricing_engine, matching_engine,
   │                          crosscheck_engine, autonomous_agent)
   ▼
SQLite (WAL mode, foreign keys, indexes)
```

## Privacy & data handling

ErrandMate stores only what it needs, and it never shows personal details to the public.

| Data | Why it's stored | Who can see it |
|---|---|---|
| Name | Shown on errands and reviews | Everyone |
| Email, phone | Login and contact | **Only the account owner** |
| Address, postcode | Profile and local matching | **Only the account owner** |
| ID number (optional) | Self-declared ID type | **Only the owner**, and only the last 4 characters are ever stored |
| Password | Login | **Nobody**: only a salted PBKDF2 hash is stored |
| Ratings and reviews | Runner reputation | Everyone (reviewer's name only) |
| Errand location | So a runner knows where to go | Everyone viewing the errand, so posters are advised to use a pickup point or street rather than a full home address |

How this is enforced:
- **Public endpoints return no contact details.** Task listings, runner matching, profiles and reviews show names and stats only.
- **Data minimisation:** full ID numbers are masked before they reach the database (`P98765432` → `*****5432`), so even a database leak can't expose them.
- **Tested, not just promised:** `tests/test_privacy.py` calls every public endpoint and fails if any email, phone, address, postcode, ID number or password field shows up.
- **No real data in the repo:** demo accounts and addresses are fictional, and database files are git-ignored.

## Security notes

- Passwords: PBKDF2-HMAC-SHA256 with a random salt (100k iterations) and constant-time comparison.
- Auth: signed HMAC-SHA256 bearer tokens with an expiry. `SECRET_KEY` comes from the environment; there's no hardcoded fallback.
- Every SQL query is parameterised.
- Permission checks on every errand action (e.g. only the poster can confirm completion, and no one can accept their own errand). The platform-wide agent toggle is admin-only.
- CORS is limited to configured origins.

**Known limitations (it's a portfolio project, not a production service):**
- ID details at sign-up are **self-declared and not verified**. Accounts are marked unverified unless seeded as demo data. Don't enter real ID numbers.
- Data is stored in plain SQLite (not encrypted at rest). A production version would add disk or field-level encryption, data-export and deletion requests (GDPR), and audit logs.
- Tokens are a hand-rolled JWT-style format. A real deployment should use a maintained library (e.g. PyJWT) and add rate limiting.
- There are no real payments; "escrow" is a status field only.

## Quick start

Requirements: Python 3.10+

```bash
git clone https://github.com/Alsndeveloper/errandmate.git
cd errandmate
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn server.app:app --reload
```

- App: http://127.0.0.1:8000
- API docs (Swagger): http://127.0.0.1:8000/docs

Or run it with Docker: `SECRET_KEY=... docker compose up --build`

### Demo accounts (local demo data only)

| Account | Login | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Poster | `poster@errandmate.com` | `Password123!` |
| Runner | `runner@errandmate.com` | `Password123!` |

To turn demo data off, set `SEED_DEMO_DATA=false`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

22 tests cover the API, the lifecycle rules, the database, security, privacy, and
the rule engines. Every run uses its own temporary database, and GitHub Actions runs the
suite on every push.

## License

[MIT](LICENSE)
