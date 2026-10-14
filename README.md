---
title: OTU Opportunity Engine
emoji: 🟢
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
---

# OTU Opportunity Engine

Release: **0.1.1** (2026-10-14). See CHANGELOG.md.

Private opportunity workspace for Desmond Glover. Matrix-inspired, high-contrast UI with a saved opportunity board, stages, contact records, follow-up dates, outreach templates, and on-demand Remotive discovery. Contra is the first contract-platform shortcut; account automation is not implemented.

Run with Python 3.12: `python app.py`. No external packages required. Check `/health` and exercise the board. Run `python -m unittest discover -s tests` for persistence and API checks.

## Hugging Face setup

Create a **private Docker Space** and upload app.py, Dockerfile and this README. The app has no built-in login: do not deploy it publicly with personal records. Connect private writable storage to this Space. If Hugging Face confirms its mount path is `/opportunity-data`, set the Space variable `OTU_DATA_DIR=/opportunity-data/otu-engine`. Use the actual mount path shown by Hugging Face; setting a variable alone does not mount a bucket. Default `/tmp` storage is temporary and can disappear on restart/rebuild. Free Spaces may sleep; this is not an always-on autonomous service.

Keep résumés and career archives in private storage, not a public repository. No email, AI provider or platform credentials are required for this first version. It prepares drafts and opens your email app; it does not send messages or attach documents. Check recipient, original listing, prior outreach and attachments yourself. No applications are auto-submitted. No invented outcomes or sample leads are seeded.

## Next connections

Contra discovery/proposals require an authorized account workflow and verification of supported access. Dedicated inbox recommended (e.g. opportunities@your-domain): connect through provider OAuth in a future iteration for reply tracking and approved sending. Never paste passwords into chat. Portfolio assets, career-document retrieval, AI-assisted proposal tailoring, scheduled discovery, activity history and income reporting remain implementation work.
