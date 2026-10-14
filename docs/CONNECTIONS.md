# One-time private connections — v0.2.0

## Career library

Open the Space app → Career library → Import privately. Upload OTU-Career-Library-v1.zip (prepared separately, never committed here), or upload the original archive and résumé files. The master archive alone is enough to generate new applications; the designed examples are optional. Generated résumés and cover letters appear in Review & send. Existing documents are deduplicated by checksum. Inspect originals before attaching them. The full master is an internal source, not a ready-to-submit résumé.

## Hugging Face inference

Create a separate fine-grained Hugging Face token with **Make calls to Inference Providers** permission. Save it in the Space's **Secrets** as `HF_INFERENCE_TOKEN`. Do not use the GitHub deployment token as an app credential.

Optional Space **Variable**: `HF_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507:scaleway`. Provider availability was confirmed from model metadata on 2026-10-14; it can change. Check your account's Inference Providers credits/billing before a request. Membership is not proof of unlimited inference.

In the app, import career files and a real listing, then click **Tailor with AI**. A configured token is not proof of a working connection. Review factual claims before approval. Maximum 700 output tokens and 10 attempts/day; there is no automatic AI drafting.

Official references:
- https://huggingface.co/docs/inference-providers/tasks/chat-completion
- https://huggingface.co/settings/tokens
- https://huggingface.co/settings/inference-providers

## Existing Gmail / Google Workspace inbox

1. In Google Cloud Console select/create a project, enable **Gmail API**, and configure the OAuth consent screen for your use.
2. Create an OAuth client of type **Web application**.
3. Use the Space's **direct app URL**, not huggingface.co/spaces/... . For this Space the expected hostname is `https://dezz-9-10-otu-opportunity-engine.hf.space`; confirm the address in Hugging Face's Open App link.
4. Authorized redirect URI: `https://dezz-9-10-otu-opportunity-engine.hf.space/oauth/google/callback` (must exactly match).
5. Add the scopes `https://www.googleapis.com/auth/gmail.send` and `https://www.googleapis.com/auth/gmail.readonly`. Add your Google account as a test user if the consent app is in Testing. Google may require additional verification or organization admin approval; testing refresh tokens can have limited lifetimes.
6. In private Space **Secrets**, save `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. In **Variables** save `PUBLIC_URL=https://dezz-9-10-otu-opportunity-engine.hf.space`.
7. Open app → Connections → Connect your inbox. Authorize the intended Gmail account; never put your Gmail password in the app or chat.
8. Gmail is connected only after the callback succeeds. Prepare a draft, inspect attachments and recipient, approve the exact saved draft, then explicitly send. For an initial end-to-end check, send to an address you control and verify the message and attachment actually arrive. Inbox sync is manual.

OAuth tokens stay in the private database and are excluded from exports. Disconnect removes the local binding; revoke consent in your Google Account if you want to revoke access at Google as well. Use one owner and one running Space instance.

Official Google references:
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/workspace/gmail/api/guides/sending
- https://developers.google.com/workspace/gmail/api/auth/scopes

## Contra

No token or password field is implemented. Use the account's supported interface. The official guide says job-feed filters include tools, skills and budget, with Apply/Dismiss actions. DMs are not intended for pitching services.

If your account has **Co-Agent**, open its **Connectors** section and inspect supported connections before assuming an outbound Contra API exists. The help article describes Co-Agent connecting to MCP tools; that is not evidence this app can control Contra. Do not bypass login checks or platform restrictions.

Use the app to save requirements, evaluate fit and prepare proposals; manually apply on Contra and record completion until account automation is verified.

Official Contra connector link: https://contra.com/co-agent/connectors . The public help article confirms inbound MCP tool connections for Co-Agent; it does not establish that this app can read or submit Contra applications. Profile → Share Profile is the documented way to copy a profile link.
