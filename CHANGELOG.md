## v0.18.0

- Retrieve bounded source-labeled excerpts from the current career master, confirmed career updates, exact-conversation owner notes and explicitly enabled TXT/MD files. Exclude AI replies as factual evidence and keep other threads/platforms isolated.
- Save supplied references with each response and show a collapsed Sources section. Preserve source dates, version digests and uncertainty; no automatic career edits or model training.
- Add Let Isis read this / Stop using in chat for small UTF-8 text files with explicit provider-sharing confirmation. Other formats stay stored/previewable and clearly unread by chat. Complete backups preserve opt-in records and answer references.
- Add 28 synthetic offline retrieval scenarios, source/persistence/privacy/budget tests and browser checks. Keep existing model, hardware, inference-call limits, approval controls and original data.

## v0.17.1

- Reserve independently scrolling conversation space in short windows; move workspace shortcuts into an accessible Workspace tools menu below 800 px height. Keep New chat, project filters, Help and Settings visible. Clear stale search/archive filters when creating a conversation so it cannot disappear from its list.
- Clarify conversation counts, project labels and the selected thread; keep the active conversation visible after list refresh. Preserve all threads and allow the owner to remove duplicates manually.

## v0.17.0

- Acknowledge Send immediately: show the question in chat, clear the composer, and display a real pending indicator. Save request receipts and questions before inference; poll status without additional model calls. Duplicate sends reuse the same request ID; no automatic provider retries.
- Keep replies in their original chat, preserve the next typed draft and open panes, and reconnect to acknowledged pending requests after refresh. Interrupted server work is labeled rather than silently restarted.
- Put Copy, Read aloud, thumbs up/down and More together in a reachable response toolbar. Support copying user messages and a message-specific manual-copy fallback on Safari. Render simple bold text safely.
- Persist scoped per-response ratings, include recent ratings as conversational guidance, and preserve ratings/request receipts through backup recovery with note-ID remapping. Ratings are not factual verification or model training.
- Strengthen grounding: prior AI replies do not verify identity/wallet/payout, agreed pay/hours or a prepared 90-day plan. Continue existing Contra materials and label unsupported claims as unverified.
- Add delayed-provider browser coverage for immediate acknowledgement, preserved drafts, response controls, clipboard fallback, failures, no automatic retries, navigation isolation and reload recovery. No paid inference or client outreach used in checks.

## v0.16.2

- Name the AI teammate Isis (she/her), with a warm, confident adult American persona; preserve OTU product branding and existing history.
- Prefer known female American English voice names when available and add a saved per-browser voice choice, preview and Stop under Isis’s voice. Voice gender/age cannot be guaranteed by the browser; show the selected voice and a transparent fallback. No paid speech API, new token or conversation migration.

## v0.16.1

- Balance reference-inspired proportions: 18 px conversation text (17 px on phones), readable sidebar labels and project fields, a compact composer, and consistent side-panel typography.
- Keep editable controls at least 16 px to avoid iPad focus zoom, and use 44 px action targets without removing controls. Keep pinch zoom, pane behavior and keyboard positioning intact.
- Let navigation scroll on short screens so controls stay reachable when the keyboard reduces the visible area. Preserve all existing conversations, projects, mail, files and settings; no data migration.

## v0.16.0

- Add project grouping, multiple chats per project and a Move menu for touch/desktop; preserve original workspace, opportunity, messages and file links, including older conversations.
- Add conversation options through three dots, right-click or long-press: Rename, Pin, Move, Archive, recoverable Delete and Restore from Trash. Keep unfinished messages when organizing.
- Add Mail: Gmail Inbox/Sent/search, full plain-text threads, OTU Drafts/Outbox, local folders, opportunity links, follow-up dates and Open Gmail. Reuse exact-draft review/send protections; no extra scopes, Gmail label edits, automatic sends or paid AI browsing.
- Stream complete credential-free backup ZIPs with completed conversation files; verify checksums before recovery, merge organization metadata and remap opportunity/file links. Preserve a pre-upgrade checkpoint and pre-restore checkpoints. Recovery currently accepts ZIPs up to 1 GiB through the UI and 95 MiB total career files; larger backups require developer assistance.
- Add runtime checkpoint-preservation reporting and browser checks for long-press, project movement, archive/Trash recovery, Mail folders and unchanged chat scope/draft text.

## v0.15.0

- Load reconciled owner handoff knowledge and an evidence-labeled Contra status report into the conversational assistant; preserve existing records and distinguish applications, unsent drafts, conflicting decisions and unverified opportunities.
- Add Where we stand to the conversation menu using the existing side panel, without AI calls or new setup.
- Define a warm, practical conversational personality and multi-platform guideline-first planning policy; do not restart existing Contra setup or invent action capabilities.
- Bound chat knowledge by selected opportunity and use smaller context for document/proposal revisions to control usage and preserve isolation.
- Add per-answer browser/device Read aloud, Pause, Resume and Stop. Stop playback on chat changes/background and prevent dictation/playback overlap. No HF/OpenAI speech API, new token or paid smoke test.

## v0.14.0

- Rebuild the viewport shell around one persistent chat, with a collapsible desktop icon rail and tablet/phone navigation overlay.
- Move supporting sections into an independent side pane: chat, draft text and scroll position are preserved when browsing tools. Separate workspace browsing state from active conversation scope.
- Remove inherited dashboard centering and repeated chat headings/actions; align panes with the screen edges, use compact anchored menus and a lower-profile composer, and quiet the Matrix background.
- Coalesce visible-viewport changes, preserve message scroll anchoring and account for Safari pan offsets without programmatic page scrolling. Keep pinch zoom enabled and avoid opening the keyboard automatically on New chat.
- Add responsive panel focus/escape/backdrop behavior, tablet document-to-chat dismissal, native-dialog precedence and persistent version access through the conversation menu.
- Save a reproducible localhost-only browser fixture at scripts/check_workspace_ui.py. No inference is called by the fixture.

## v0.13.0

- Simplify navigation into New chat, Opportunities, Library, Connections and Explore, with Help/settings below; enlarge navigation/chat text and keep recents focused on conversation names.
- Add the composer file picker, scoped attachment lists and private decoded photo previews. Device-configured cloud providers are accessible through the native Files picker; no new Drive OAuth integration is claimed.
- Add resumable/idempotent 4 MiB upload chunks, up to 1 GiB per file, a default 5 GiB app allowance, progress, partial cancellation, persistence, streamed downloads and a storage meter. Actual bucket capacity still applies. Conversation uploads are stored separately from legacy backup ZIPs and never automatically sent to AI.
- Add a navy/gold two-column PDF résumé design and matching styled editable Word layout. Use actual master contact details, chronology, education and capabilities; preserve prior files and generate only for a selected opportunity.

## v0.12.0

- Anchor the app to Safari's visible viewport and keyboard pan offset; coalesce resize events, prevent programmatic focus scrolling and use readable input sizes without disabling pinch zoom.
- Add browser speech dictation with editable text, visible listening/stop state, permission/error guidance and keyboard dictation fallback. No automatic send or paid transcription provider.
- Generate fresh opportunity-specific application packages; rank source facts against listing requirements, preserve versions, label past examples, remove old résumé auto-attachments and block unrelated résumé/cover-letter attachments during approval.
- Keep application generation visible inside opportunity conversations. Master files remain unchanged; existing confirmed-update controls remain in place.

# Release history

## 0.11.0 — 2026-10-15

- Make conversation the default workspace with a persistent recent-chat sidebar, separate new threads, search, rename and restored last conversation. Preserve original conversations and scoped memory in backups.
- Add decorative Matrix character rain with reduced-motion support, a saved pause control and background-tab suspension.
- Review documents beside chat on larger screens and in an accessible mobile sheet, with preserved revision and approval controls.

## 0.10.1 — 2026-10-15

- Include the current prepared proposal in its opportunity chat and add reviewed proposal revisions alongside document revisions. No message changes are saved or sent without review.

## 0.10.0 — 2026-10-15

- Add Talk to OTU with curated project memory, scoped remembered instructions, and owner-reviewed developer requests/replies through the private repository. This does not provide live private ChatGPT access or wake an agent.
- Add in-app text/PDF previews and reviewed document revision versions; retain originals and revoke unsent attachment approvals after revisions.
- Reuse existing credentials and deployment runs for request sync; no scheduled background agent or paid inference tests.

## 0.9.5 — 2026-10-15

- Read full block-based descriptions, format Contra budget amounts, and surface current service/portfolio counts.
- Verify application state using the exact GeekyAnts job ID and visitorDidApply flag rather than matching a name or assuming historical delivery.

## 0.9.4 — 2026-10-15

- Include challenge deadlines/prizes, broader feeds and a first client-conversation read; fetch a bounded set of full job descriptions.
- Keep partial read failures visible and distinguish missing confirmation from a completed application.

## 0.9.3 — 2026-10-15

- Show extracted Contra opportunities with original links and a reviewed save action; keep incomplete listings marked as needing verification.
- Avoid caching malformed AI responses.

## 0.9.2 — 2026-10-15

- Inspect read-result structure and extract canonical public opportunity links while keeping private account content on the mounted volume.

## 0.9.1 — 2026-10-15

- Reuse identical successful AI requests for six hours and bound reference excerpts before inference to reduce unnecessary usage.

## 0.9.0 — 2026-10-15

- Share atomic persistent AI request/token reservations across chat and proposal writing, with a pause switch and owner-visible limits; no paid inference in deployment checks.
- Add conversation modes for reviewed replies, possible questions and negotiation preparation.
- Add a fixed read-only Contra inventory/feed check, cached for 30 minutes; keep account responses private.

## 0.8.1 — 2026-10-14

- Verify authorized Contra access during deployment and record tool definitions for integration planning, without invoking account tools or exporting account records.

## 0.8.0 — 2026-10-14

- Verify Contra’s MCP endpoint and OAuth metadata, register a public app client, and add Connect Contra with PKCE sign-in.
- Discover available tools after owner authorization; no account tools are invoked and no messages, applications, or publications are performed.

## 0.7.3 — 2026-10-14

- Encode device bookmarks safely and validate them as actual JavaScript bookmark URLs, including the cross-origin reader workflow.

## 0.7.2 — 2026-10-14

- Add no-subscription device-browser reader and profile-filler tools, with registered-origin handshakes, explicit capture review, and a Safari setup guide.
- Keep hosted browsing behind its unverified-hosting notice after the live sandbox check failed.

## 0.7.1 — 2026-10-14

- Strip application secrets from the browser subprocess environment and reset page approvals when opening a platform.

## 0.7.0 — 2026-10-14

- Add career-based platform profiles and future-platform registration.
- Add sandbox-required assisted browsing, visible-page listing extraction, reviewed profile/message filling, and employer-ready file attachment.
- Keep automatic discovery limited to verified public feeds; account creation, applications, consent and login challenges require owner interaction.
- Browser login sessions are not persisted; production availability must pass the live runtime check.

## 0.6.1 — 2026-10-14

- Keep account tools under one menu, show successful AI checks plainly, explain service failures without backend jargon, and include reviewed Contra help in its assistant context.

## 0.6.0 — 2026-10-14

- Simple daily navigation, plain-language Help, and honest connection cards.
- Separate platform workspaces and opportunity conversations with private notes, original emails, and optional scoped AI answers.
- Technical controls require a deliberate, expiring developer unlock; workspace notes survive private backups.


## 0.5.4 — 2026-10-14

- Resume recently read threads after Google rate limits instead of repeating requests; pace new reads and keep imported conversations monitored during partial reviews.

## 0.5.3 — 2026-10-14

- Pace Gmail history reads, retry rate-limit responses, exclude legacy chat entries, and expose safe API denial reasons.

## 0.5.2 — 2026-10-14

- Include recent conversation context in AI drafts and clarify offer terms without accepting them.
- Continue past unreadable threads and report partial review accurately.

## 0.5.1 — 2026-10-14

- Keep separate Gmail threads as distinct leads, retry temporary read failures, refresh known conversations, and recover interrupted reviews.

## 0.5.0 — 2026-10-14
- Study sent career outreach and complete reply threads, prioritizing Buffalo Stallions.
- Private conversation tracking, source-labeled progress evidence and outreach style examples.
- History-aware follow-ups, paperwork replies, duplicate checks and Gmail reply threading.
- No automatic sending or inferred paid outcomes.

## 0.4.0 — 2026-10-14
- Generate designed résumé and cover letter in PDF and DOCX directly from the master record.
- Prepare an unsent email with both PDFs attached; check document length, required names and internal-note exclusion.
- Preserve the original master and maintain source-labeled confirmed career updates.
- Add official Contra connector and profile-sharing guidance; no account access is implied.

## 0.3.1 — 2026-10-14
- Replace blank-tab JavaScript OAuth flow with a direct server redirect to Google.
- Existing Gmail credentials and required redirect URI remain valid.

## 0.3.0 — 2026-10-14
- Guided setup: career files, optional AI writing, Gmail sign-in.
- Plain-language progress labels and message actions; technical settings collapsed.
- Direct ZIP-upload instructions, file counts and upload progress.
- Actionable connection buttons, mobile setup layout and clearer saving status.
- No new paid provider calls, automatic spending or outbound sending.

## 0.2.1 — 2026-10-14
- Add database and file storage markers for automated first-launch restart validation.
- Report production opportunity counts and actual source-check results.

## 0.2.0 — 2026-10-14
- Private career-file ingestion and retrieval; original documents preserved.
- Persistent storage checks, record migration, backup and merge recovery with delivery history.
- Ranked public-source discovery and Contra official-help playbook.
- Editable proposal templates and optional Hugging Face inference.
- Exact-message approval, attachment checks, duplicate controls, Gmail OAuth and reply matching.
- Responsive Matrix dashboard with next actions, stage tracking and activity history.
- Awake-only background discovery; no automatic outreach.
- Deployment workflow validates app dependencies, UI syntax and runtime separately.
- Gmail, inference, production career import and restart persistence require one-time connection/validation. Contra account automation remains unimplemented.

## 0.1.1 — 2026-10-14
- Add visible release version to the app footer and health response.
- Add VERSION, release checksums, and a numbered download package.
- Correct storage instructions to use the actual connected bucket mount path, with /opportunity-data/otu-engine as the configured example.
- Includes the JavaScript string-escaping fix made during initial development.
- No new opportunity automation, account connections, or outbound sending.

## 0.1.0 — initial unnumbered delivery
- Matrix-style opportunity board, manual leads, duplicate-link prevention, stages, follow-ups, template outreach, platform links, and Remotive adapter.
- Earlier uploaded copies were not versioned; their contents cannot be confirmed from this workspace.
