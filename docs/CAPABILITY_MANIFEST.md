# OTU / Isis capability contract — v0.19.0

Purpose: help the private owner assess earning opportunities, prepare accurate materials and track confirmed progress. This is a local capability manifest, not a deployed JOAT Agent Factory or new agent hierarchy.

## Implemented conversation capabilities

- One budgeted hosted writing request per explicit Send, with durable receipts and no automatic provider retries.
- Read-only local lexical retrieval from the current career master (first 100,000 characters), owner-confirmed career updates, up to 1,500 most recent owner-written notes in the exact workspace/opportunity/chat, and explicitly enabled TXT/MD uploads.
- At most four excerpts and 4,800 UTF-8 JSON bytes of retrieval evidence, further reduced if needed to fit the existing 24,000-byte message limit. Additional input can change per-call cost or consume the allowance sooner; limits and model remain unchanged.
- File reading requires explicit confirmation that excerpts may be sent to the configured provider when questions are asked. UTF-8 TXT/MD only, at most 256 KiB and 50,000 characters each, up to 20 enabled files per conversation. PDF, Word, images, archives, audio and video remain unread by chat. Career Library's previously extracted master is a separate existing source.
- Sources retain source type/authority, saved date, digest, character offset and excerpt. The collapsed Sources section shows references actually supplied, not proof that every answer is correct. Original files and notes are unchanged.
- Earlier assistant answers and application examples are excluded from retrieval evidence. Statements in files remain untrusted reference, not permissions, validated qualifications or automatic memory corrections.
- Source references survive normal refresh, reopen and recovery. Complete recovery also preserves readable-file choices and text; legacy backups omit the separate upload store. Stopping file retrieval affects future questions, not prior saved replies or an already-started request.

## Permissions and boundaries

Chat can execute bounded owner-requested research reads described below. It cannot send email, apply, create accounts, spend, publish, accept contracts, train weights or wake Codex. Existing separate platform/Mail screens and approval workflows remain unchanged. Source files cannot authorize actions. Shared career facts are owner-wide; private conversation notes and files remain exact-scope. Project metadata does not grant cross-thread access.

Human corrections can be retrieved as owner statements; contradictions must be surfaced, and explicit later corrections take priority in the model instructions. No unreviewed response becomes trusted training data. Lexical retrieval can miss paraphrases and implicit corrections; no semantic-search or model-quality improvement claim is made without measurement.

## Evaluation and acceptance

`python scripts/evaluate_otu.py`: 28 synthetic offline evidence-retrieval scenarios. It checks source presence/absence, current-master selection, older notes, scope isolation, file opt-in and bounded excerpts. It does not evaluate generated answers or actions.

`python -m unittest discover -s tests`: backend behavior, recovery, budgets, isolation, permissions and retrieval integration using mocked provider responses. Browser fixtures cover opt-in controls, source display/escaping/reload and existing chat/UI workflows. Real-model factuality, owner writing preference and actual iPad behavior still require observation under an explicitly bounded usage allowance.

## Deployment and recovery

Use existing work-branch GitHub Actions and the existing private Space. Include knowledge_store.py in Docker/deployment allowlists. Schema changes are additive: file_knowledge and work_notes.sources. No source replacement, auto-deletion or credential migration. Complete export retains new records. Do not roll back to a pre-v0.18 restore implementation and expect it to understand new export fields; retain the versioned backup and use the corresponding reader. A prior code rollback leaves stored originals in place, but its UI will not show new references.

## Next capabilities, not implemented by this release

Better model-answer evaluation, semantic retrieval if justified, broader chat-driven platform reads and reviewed draft actions, broader document processing, shared-account live billing and JOAT integration contracts. No paid hardware or model training is needed to establish this first baseline.


## v0.19.0 research contract

Direct requests beginning with find/search/research/look up/check/refresh and mentioning opportunities or a supported platform, or explicit Research opportunities mode, can route research. Source files, incoming messages, previous answers and model prose cannot select tools. The model receives returned evidence and a receipt, never a free-form executor.

Saved opportunity reads stay within the selected workspace/opportunity (My assistant may search owner-wide saved opportunity records). Private notes/files never cross conversations. Contra live reads require My assistant or Contra scope and an existing Contra connection. Unsupported platforms report the limitation. Job feed reads request five records; detail URLs must be HTTPS Contra opportunity URLs and use a validated slug. Challenge feeds provide partial listings, not verified eligibility, rights or complete rules. One primary fixed allowlisted tool call is made per request, with one additional FOR_YOU feed call only after an empty keyword job search; protocol initialization and existing token refresh are separate transport steps. No private message/profile tools or writes are dispatched.

Research caches are private runtime settings, scoped by workspace/opportunity/chat/tool arguments for ten minutes, with at most ten entries. Explicit refresh/fresh-check requests bypass the cache. All cache and read timestamps remain distinguishable from current platform verification. No records are automatically imported, applied, accepted or marked paid.

At most one writing call follows research, with the existing model and limits. Research strips unrelated email/draft/outreach context from that writing payload. If writing is disconnected, paused or exceeds current allowance, a deterministic summary is saved instead. A failed or malformed provider reply falls back without retry and without claiming zero possible charges. Original conservative accounting remains authoritative for attempts. The independent read-only preview route does not invoke a model or create chat notes.

`tests/test_research_tools.py` covers routing, allowlists, scope, caching, failure/empty distinctions, untrusted contents, budget fallback and receipt recovery. `scripts/check_research_ui.py` checks progress, source links/escaping, preserved drafts, cached reads, no extra writing call during pause and reload/phone bounds using mocks. Deployment verification records a bounded actual read separately; it does not evaluate generated recommendations.

### v0.19.2 empty-feed handling

An empty keyword job search can make one additional, fixed FOR_YOU read (five records). Two platform reads maximum, one writing call maximum; no fallback after errors, unrecognized content, job detail or challenge requests. Both checks and account accessLimitedFeed flags survive caching and backup. Broader results carry match_basis, not a claim of keyword fit. Older search caches are invalidated by a key version.

### v0.19.3 allowance handling

Allowance-blocked ordinary chat persists a labeled local notice and, where available, the last exact-conversation research receipt with previous_read status. It does not dispatch reads or inference, infer recommendations, or provide document/proposal revision IDs. Typed local allowance denials remain distinct from ambiguous provider failures; failed attempts retain reservations. Existing five-request/60,000-conservative-token defaults, model, and account-wide billing limitations are unchanged.

### v0.19.4 personal allowance

Owner approved 50 requests / 250,000 daily tokens on October 18. A one-time private settings migration preserves pause and existing usage; later manual choices survive restarts. Successful complete replies with positive integer provider total_tokens replace only their own temporary reservation. Missing/invalid measurements, incomplete replies and failed transport keep estimates. Legacy reservations are not retroactively forgiven. Warnings appear at 75% and 90% of either allowance. These are usage controls, not dollar limits or account-wide billing. Research writing context keeps owner/personality plus scoped evidence and execution receipts, omitting duplicated operating history.

### v0.19.6 opportunity review

Named application work resolves an exact Contra listing using direct URL, selected record, public saved platform inventory or research/focus from the same conversation. A conflicting selected opportunity or ambiguous selection stops before inference/read. One allowlisted job-detail read supplies returned listing text for the checklist; absent text blocks drafting. The owner request, exact title/URL, listing evidence and career sources take precedence over historical job examples. No general website or linked-file reader was added: linked guidelines remain explicitly unread until supplied/reviewed. The dated Contra Help Center guide is curated platform guidance, not client requirements or account eligibility. Known other-job names can trigger a local correction; this narrow check is not a general factual-accuracy guarantee. New result fields focus/application_review survive the existing opaque receipt backup. No AI calls or chat notes are made by the review-preview verification route.

### v0.19.7 reviewed native Contra applications

`contra_applications.py` uses fixed exact-job and applying-owner published-portfolio reads. Model prose cannot dispatch writes. Options are local, unsent form data. Preparation needs reviewed fit, a complete message, and valid returned project IDs or explicit in-conversation UI opt-out. A separate application_tools allowlist contains only apply_to_job_prepare and apply_to_job_confirm; read_tools remains read-only.

Preparation is durable before the remote call; a lost response becomes Prepare uncertain and never retries. A recognized native draftId and complete returned preview are required before submission. Submission needs owner approval of the exact preview digest, a fresh open-job/no-existing-application check, then one confirm call, then a read proving viewerApplication.appliedAt. Ambiguous outcomes become Submission uncertain; duplicate confirmations do not resend. Application receipts are scoped to workspace/opportunity/chat and native action history can ground later conversation.

The new contra_application_actions table is included in complete backup scope checks. Restores retain preview content but strip remote submission authority and mark receipts Restored. Active actions block opportunity moves. No general browser hosting fix, CAPTCHA automation, signup, purchase, invoice, DM, or model-selected executor was added. Native API fields are not a guarantee that every website-only application field was inspected.

Verification uses synthetic mocked draft/submission workflows and a trusted localhost browser. Deployment inspection reads the exact listing and portfolio only, with inspect_only avoiding even a local ticket; no real native draft/submission or paid inference is tested automatically. Actual native preview formatting and the owner’s chosen portfolio remain first-use checks.
