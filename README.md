---
title: OTU Opportunity Engine
emoji: 🟢
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
---

# OTU Opportunity Engine — v0.10.0

A private opportunity workspace for Desmond Glover. Matrix-inspired responsive dashboard for discovery, fit ranking, career retrieval, draft preparation, approved email, replies and follow-ups. Contra-first contract workflow; coaching and employment alongside it.

## Start

Python 3.12. `python -m venv .venv`, `.venv/bin/pip install -r requirements.txt`, `.venv/bin/python app.py`. HTTP `/health` reports version. `.venv/bin/python -m unittest discover -s tests` exercises persistence, migration, retrieval, approvals, duplicate prevention, recovery and API behavior. `node --check ui.js` validates browser syntax. Existing v0.1.1 records are migrated in place.

## Private storage

Keep the Space **Private**: Hugging Face access controls supply authentication; this app has no separate login and serves one owner. Connect private bucket `Dezz-9-10/otu-opportunity-data` with Read & Write access at `/opportunity-data`. Set `OTU_DATA_DIR=/opportunity-data/otu-engine`. A mount-path variable alone does not attach storage. If the mount exists the app selects this path automatically. Otherwise the default `/tmp/otu-data` is temporary and the UI warns you. A configured but missing /opportunity-data mount stops startup instead of silently storing records elsewhere.

Import the original master archive and designed résumés through **Career library**. Files are stored in the private bucket, not GitHub. Originals are preserved and indexed. Reference dossiers cannot be sent as attachments. Selected originals with internal verification notes are blocked from sending. AI receives selected, scrubbed career text only when requested; review its output for accuracy.

Use Connections → Download private backup before major changes. Exports include records, originals and delivery history, but exclude Google OAuth tokens. Restore merges records, preserves sent/unresolved delivery history and resets unsent approvals. Reconnect Gmail after recovery. Run only one app instance against this SQLite store; do not share the database with another bot. Verify a saved lead survives a Space restart before relying on storage.

## Connections

- **Contra:** official help playbook included. Job feed → Apply is the documented route. DMs are for networking, not service pitches. Account/browser automation is not connected. Co-Agent/MCP access is account-dependent and remains to investigate.
- **Public feeds:** We Work Remotely RSS response verified in research. Remotive returned 403 in research and is supplementary. The UI shows actual success/error status. A score is a keyword-based relevance aid, not a hiring prediction. Location, pay and required credentials need checking against originals.
- **Background checks:** enabled by default, at most every 12 hours while the app is awake; disable in Connections. Free Spaces can sleep. No always-on guarantee and no background sending.
- **AI:** add separate `HF_INFERENCE_TOKEN` Space secret with Inference Providers permission. Optional `HF_MODEL` variable; default `Qwen/Qwen3-235B-A22B-Instruct-2507:scaleway`, whose provider availability was checked 2026-10-14. Provider access and credits must be verified by a successful draft. Calls may incur costs; 700 output tokens maximum, 10 attempts/day. No AI calls occur until you click Tailor with AI.
- **Gmail:** see docs/CONNECTIONS.md in the GitHub repository. Configure OAuth, then authorize from the app. Exact draft approval and an explicit Send click are required. Sender account is the account you authorize. Gmail acceptance is not proof of recipient delivery. Uncertain sends are locked, never automatically retried. Inbox sync matches recent messages by saved contact address; do not assume all replies are classified correctly.

## Deployment

GitHub `work`/`main` changes trigger deployment to the existing private Space through Actions secret `HF_TOKEN`. Runtime files are explicitly allowlisted; no career archives or databases are uploaded by this workflow. Health verification is recorded separately from successful upload. See docs/DEPLOYMENT.md and CHANGELOG.md.

## Finished applications

Create finished application generates a source-grounded PDF/DOCX résumé and matching cover letter plus an unsent email from the master record. Earlier designed résumés are optional examples. Checks enforce a two-page résumé limit, one-page cover letter, required names and absence of internal notes. These are automated checks, not independent verification of every career claim. The master is preserved; source-labeled confirmed updates are versioned separately and merged into future applications. Planned projects remain planned, and application activity is never treated as employment or revenue.

Sent-history study reads career/contract Sent queries and all messages in matching threads. Full bodies stay in the private database and backups, never source code. Automated replies are distinguished from human replies; detected interview/offer wording is not proof of hiring or payment. Imported threads are tracked with Gmail links. No study action sends messages. Maximum ten query pages; the result reports whether the page limit was reached.
