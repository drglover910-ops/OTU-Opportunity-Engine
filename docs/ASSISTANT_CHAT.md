# Talk to OTU — v0.10.1

Open **Talk to OTU** for the main assistant. It receives the curated project decisions in `assistant_knowledge.json`, recent opportunity summaries, saved outreach-style examples, and current connection indicators. Platform and opportunity chats keep their own history, emails and remembered instructions. The main chat can see opportunity summaries, not other chats' private messages. Use **What to remember in this conversation** for up to eight persistent instructions without an AI call. Recent dialogue is bounded rather than repeatedly transmitting the whole archive.

The assistant is powered by the configured HF inference provider, not a live connection to the private ChatGPT thread. It has bounded read-only research tools for saved opportunities and supported Contra listings; it has no sending or account-changing tools. It can advise, draft replies, anticipate possible questions and prepare negotiation options; it cannot silently send, spend, apply, publish, summon an agent, accept a deal or train model weights. Shared project memory is updated through deployment, with a visible version. All writing calls use the shared allowance, pause control and cache. A full document rewrite may reserve up to2,000 output tokens instead of the normal700. No paid smoke tests or background inference runs are enabled.

## Read and revise without downloading

**Ready to send → View finished documents → View résumé / View cover letter** opens the reader. Read/edit text in place or select **See designed PDF** for the last saved layout. **Ask the bot for changes** opens the correct opportunity chat with that document as context. The bot returns suggested text; **Review suggested document changes** loads it into the editor. Nothing changes until the owner reviews the complete text and selects **Save as a new version**. Matching PDF and Word versions are generated in the app style, originals retained, current package links updated, and unsent attachment approvals reset. This does not edit the master career record. Source external designs may differ. Revisions require factual review and are not presented as automatically certified.

## Request development work

In chat, open **Request a development change**, or turn an assistant answer into a draft request. Review the exact text and check permission to share it to the private repository. Only that text and routing metadata transfer; emails, documents and complete chats are not included automatically. Requests persist on mounted storage and in backups. The bridge verifies the repository is private, transfers on a deployment or manual GitHub workflow run, and returns a receipt. The developer can commit a response which appears in this panel after sync/refresh. See `docs/assistant_bridge/README.md`.

There are no scheduled worker runs or autonomous developer starts. For immediate transfer, the link opens GitHub's bridge workflow: choose **Run workflow**. A copied handoff is the fallback. Receiving a request is not the same as completing it; statuses make that distinction. Existing GitHub Actions runners and authentication are reused; no new app token, subscription or OpenAI spending is required by this implementation. Existing runner usage remains subject to the account's normal allowance.

Prepared proposals have a **Discuss or revise this proposal** button. The correct opportunity chat receives the selected saved proposal. **Review revised proposal** loads suggested wording into the message editor; it is not saved until **Save my edits**, which resets approval. It never sends the proposal automatically.


## Working knowledge and voice — v0.15.0

The header menu now includes Where we stand, backed by the reconciled, dated shared working record. It does not perform a live account audit or use inference. Conversational context includes the relevant working status, personality and platform operating policy. A selected opportunity excludes unrelated status records; revisions use a smaller knowledge payload. Latest owner corrections and verified records take precedence over old snapshots. No raw ZIPs, inbox transcripts or master contact documents are added to the shared knowledge file.

Assistant replies include Read aloud, Pause/Resume and Stop, using browser speech synthesis. A local voice is preferred where available; available voices and whether browser/vendor speech processing is online vary by device. No Hugging Face/OpenAI speech endpoint is called. Reading stops on conversation changes/background, and dictation/playback stop each other. No audio is recorded or stored by this feature. Actual Safari speech quality and playback support require owner-device confirmation; Chromium tests mock speech interfaces rather than claiming microphone/speaker hardware validation.


## v0.18.0 source lookup

See [the capability contract](CAPABILITY_MANIFEST.md). Chat now receives bounded relevant career/owner-note excerpts and explicitly enabled TXT/MD reference text. Sources for this reply exposes the supplied references. Retrieval is local and makes no extra inference call; adding excerpts can increase the tokens in the one existing request. Other upload formats remain unread in chat. No platform action tools or model training are added.


## v0.19.0 research in conversation

Ask “Find Contra opportunities for GoHighLevel work” or select Research opportunities under message Options. Open Sources for this reply for execution receipts and original listing links. Research can search saved opportunities and run one supported Contra read. It cannot submit, contact, spend or edit accounts. Cached results are labeled. If writing is unavailable, the app returns a plain research summary without a second attempt. This supersedes the older statement that chat has no read tools.

Follow-up questions can reuse the last completed research receipt from the same conversation. These sources are labeled as previous reads, never a fresh platform check.

Requests may begin with “Isis, find …”. Research replies display app-generated check status. Empty research returns a direct summary without model writing; a future live check is never scheduled by the generated answer.
