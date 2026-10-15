# Native Contra connection — v0.8.0

Anonymous protocol discovery independently verified https://contra.com/mcp: initialization requires authorization, and Contra publishes protected-resource and OAuth metadata. See CONTRA_MCP_DISCOVERY.json. This is a working protocol endpoint, not merely a claim from Co-Agent.

The app registers a public OAuth client using the advertised registration endpoint and its configured PUBLIC_URL callback. It uses authorization-code flow with S256 PKCE, random ten-minute one-use state, and token refresh. No password or manually copied token is required. Private stored connection settings are excluded from backups and never returned by status endpoints.

Connections → Connect Contra opens Contra’s own consent page. Review its permissions. After returning to the bot, Check Contra access initializes MCP and lists available tool definitions. This release does not invoke tools/call at all: no profile reads or edits, searches, messages, applications, publications, invoices or payments are performed through the connector yet. The next implementation step is mapping the actual discovered read tools, rather than inventing tool names or schemas. Do not treat broad mcp:tools authorization as approval to perform write actions.

Co-Agent AI conversation history remains unverified/unavailable; business/client-message tools must not be mistaken for the AI transcript. Preserve the imported handoff and existing profile/portfolio work. No need for another export.

Disconnect removes stored access locally. It does not claim to revoke server-side permissions; the owner can revoke those through Contra. A signed-in status is distinct from a successful capability check.
