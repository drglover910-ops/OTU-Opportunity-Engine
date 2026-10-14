# Platforms, profile builder, and assisted browsing — v0.7.0

Supported starting catalog: Contra, PeoplePerHour, Upwork, Indeed, LinkedIn, Remotive, and We Work Remotely. The first five were named in the owner’s original handoff. Future public HTTPS platforms can be registered with their own workspace.

Prepare my profile uses the existing master career record and saves a separate editable profile per platform. It does not invent rates, licenses, qualifications, or create an account. Review and save the details, then use Fill my saved profile on a supported signup form. Passwords, identity checks, legal agreements, payment steps and final account creation remain owner actions.

The assisted browser is a single-owner Chromium session. It starts only on demand and requires Chromium’s sandbox in production. It does not use stealth, bypass platform challenges, or persist a login profile. Login sessions end on browser/Space restart. If the runtime cannot provide the sandbox, browser use fails closed; do not enter credentials. The app’s profile preparation, external platform links, manual listing import and verified public feeds remain usable.

Read this page extracts rendered page text and possible listing links for owner review. It does not read hidden API responses, crawl a full platform, or establish that platform rules permit bulk collection. Review a listing’s company, title, requirements and URL before saving. Existing URL deduplication applies. Automated discovery remains the existing We Work Remotely and Remotive adapters while the Space is awake.

The browser can fill supported profile fields, place a prepared application message, and attach employer-ready files. It never fills passwords or identity/payment fields from stored profiles or accepts checkboxes. Review is required before filling or attaching; submission-related buttons require a separate, one-use approval. The app reports attempts rather than claiming account creation or application submission without confirmation.

Tests use a locally fulfilled fixture, without contacting a platform. The fixture explicitly disables the sandbox only because the local test runner is root; production requires it. Deployment tests a fresh anonymous Contra page only if no owner browser session is open, closes its test session, and reports browser/runtime restrictions separately from app health. No account is created and no platform application is submitted by deployment checks.
