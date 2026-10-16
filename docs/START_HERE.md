# Start here — v0.3.0

Open your private Space and refresh. Get set up guides you through the steps below. You do not need to upload another release; GitHub deploys updates.

## 1. Career files

Career library → Choose your ZIP or résumé files → Add my career files. Select your original JOAT_Professional_Career_Archive_FIXED.zip as-is. The master ZIP is sufficient for generating finished résumés and cover letters. Older designed PDFs/DOCXs are optional examples. Multiple files can be selected together. Wait for the uploaded-file count. Originals are preserved. ZIP members are opened by the app, not by you.

## 2. Optional AI writing

At Hugging Face Settings → Access Tokens, create a fine-grained token named otu-opportunity-writing with Make calls to Inference Providers permission. In this Space's Settings → Variables and secrets → New secret, save it under HF_INFERENCE_TOKEN. Keep it out of chat and GitHub files. Return to Get set up and click Check my connections. After importing career files, try Write with AI on one real opportunity and inspect its accuracy. The default model is already chosen; no model-variable entry is needed unless changing providers/models.

Searching and basic draft templates do not use a paid AI API. AI requests can consume credits and incur provider costs. Five shared chat/writing attempts per UTC day is the default local request limit, not a dollar spending cap. Connections includes a pause switch and adjustable request/token allowances; identical successful requests can be reused for six hours. Other projects’ spending and the account balance are not available inside this bot. Check Hugging Face's Inference Providers account/billing settings before requesting AI writing. OpenAI is not connected or charged.

## 3. Gmail — one-time Google registration, then sign-in

1. Google Cloud Console: select/create project OTU Opportunities.
2. APIs & Services → Library: enable Gmail API.
3. Google Auth Platform / OAuth consent screen: configure the app. For a personal Gmail account choose External, stay in Testing, and add your own Gmail as a test user. Workspace organizations may require their administrator's approval.
4. Data access / scopes: add https://www.googleapis.com/auth/gmail.send and https://www.googleapis.com/auth/gmail.readonly.
5. Clients / Credentials: create an OAuth client, type Web application. Authorized redirect URI: https://dezz-9-10-otu-opportunity-engine.hf.space/oauth/google/callback.
6. Copy its client ID and client secret into private Hugging Face Space Secrets named GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET. Add regular Variable PUBLIC_URL with value https://dezz-9-10-otu-opportunity-engine.hf.space. Do not paste these credentials in chat.
7. Return to app → Get set up → Check my connections → Sign in with Google. Choose the intended inbox and authorize it.

After that, daily use is sign-in-free while consent remains valid. Google can expire testing authorizations or require reauthorization. A public service will need the applicable verification before general customer use.

## Daily work

Today → Review an opportunity → Read the original listing → Create finished application → Save my edits → Approve this message → Send approved email. For Contra, copy the reviewed proposal and submit it through the platform's Apply workflow. Set your follow-up date and review replies. Preparing or approving a message does not send it.


## Current chat-first interface (v0.11.0)

Refresh the app to open your conversation. Use **New conversation** for a separate thread, **Recent conversations** to return to work, and **···** to rename a new thread. On a narrow screen, tap **☰** for the sidebar. Existing opportunity conversations remain available through Opportunities and the original conversation entries.

Use **Ready to review → View finished documents → View résumé / cover letter** to read the actual designed pages in the app. **Ask the bot for changes** opens the relevant opportunity chat; review suggested wording before saving a new document version. On a phone, Back to conversation closes the review sheet. No download is required. **Conversation tools** holds remembered instructions and development requests; **Options** beside Send holds writing modes and free note saving.

**Pause Matrix / Play Matrix** controls the falling characters. The choice is saved on this device. Reduced-motion settings are respected by default. The background does not use AI credits. Existing writing allowance and pause controls remain in Connections.


## Daily use in v0.16.0

Open the private app at https://huggingface.co/spaces/Dezz-9-10/OTU-Opportunity-Engine and refresh once after an upgrade. No reconnection or upload is needed for existing saved work.

Choose a project above recent conversations, then New chat to start another conversation there. Use three dots or hold a conversation still briefly to Rename, Pin, Move, Archive or Delete. Delete moves it to Trash; select Trash above the list and Restore to bring it back. Projects group conversations; their original opportunity, messages and files remain together. Use Move on iPad. Desktop dragging onto the project selector also opens the destination chooser.

Open Mail for Inbox or Sent. Search / refresh loads current Gmail results. Open a conversation to read its messages; Open Gmail handles Gmail-only drafts and mail attachment downloads. OTU drafts and Outbox lead to the existing review-and-send screen. Approved messages do not send themselves. Folder assignments and follow-up dates are private OTU organization, not Gmail changes.

Connections → Download a private backup includes completed conversation uploads. Developer tools also offers complete-backup recovery. Recovery merges existing work and resets unsent approval; a checkpoint is kept before restoring. The UI accepts a backup ZIP up to 1 GiB, with 95 MiB total career files during recovery. Larger ZIPs need developer help. Keep your backup private; account credentials are excluded.
