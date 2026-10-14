# One-time deployment connection

GitHub repository: drglover910-ops/OTU-Opportunity-Engine.
Target private Space: Dezz-9-10/OTU-Opportunity-Engine.

In GitHub repository Settings → Secrets and variables → Actions → New repository secret, save HF_TOKEN with a Hugging Face fine-grained token allowed to read/write the target Space. This is separate from Codex environment secrets. Never add it to files, chat, or a regular repository variable.

Open Actions → Deploy private Hugging Face Space → Run workflow, select work (or main when that branch contains the workflow). Pushes changing deployment files on work/main also trigger deployment. A successful upload is not proof that the Space finished building. The workflow now checks the private app runtime and records the result in docs/LATEST_DEPLOYMENT.json; first-launch checks also test persistent storage across a restart. Check Hugging Face runtime and persistent storage separately.

The script refuses to deploy to a public Space and uploads only the explicitly listed application, UI, dependency and release files in scripts/deploy_space.py. Career archives, databases and secrets are excluded. It does not change the Space's storage, variables or privacy. Keep OTU_DATA_DIR pointed at actual connected private persistent storage.

This pipeline bypasses the Codex-to-Hugging-Face network-secret binding. It still requires a valid Hugging Face token. If it reports authentication failure, diagnose token validity or scope from GitHub/Hugging Face; do not repeatedly recreate Codex entries.
