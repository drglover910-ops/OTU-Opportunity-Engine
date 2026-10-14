# Start here — v0.3.0

Open your private Space and refresh. Get set up guides you through the steps below. You do not need to upload another release; GitHub deploys updates.

## 1. Career files

Career library → Choose your ZIP or résumé files → Add my career files. Select your original JOAT_Professional_Career_Archive_FIXED.zip as-is. Select the designed résumé PDFs/DOCXs separately if they are not in that archive. Multiple files can be selected together. Wait for the uploaded-file count. Originals are preserved. ZIP members are opened by the app, not by you.

## 2. Optional AI writing

At Hugging Face Settings → Access Tokens, create a fine-grained token named otu-opportunity-writing with Make calls to Inference Providers permission. In this Space's Settings → Variables and secrets → New secret, save it under HF_INFERENCE_TOKEN. Keep it out of chat and GitHub files. Return to Get set up and click Check my connections. After importing career files, try Write with AI on one real opportunity and inspect its accuracy. The default model is already chosen; no model-variable entry is needed unless changing providers/models.

Searching and basic draft templates do not use a paid AI API. AI requests can consume credits and incur provider costs. Ten attempts/day is a request limit, not a spending cap. Check Hugging Face's Inference Providers account/billing settings before requesting AI writing. OpenAI is not connected or charged.

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

Today → Review an opportunity → Read the original listing → Write a basic message or Write with AI → Save my edits → Approve this message → Send approved email. For Contra, copy the reviewed proposal and submit it through the platform's Apply workflow. Set your follow-up date and review replies. Preparing or approving a message does not send it.
