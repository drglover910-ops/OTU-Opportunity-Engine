# Chat-first Matrix UI direction — 2026-10-15

Owner supplied a screenshot of the ChatGPT/Codex workspace and requested analysis/research before redesign. This is a design specification, not a claim the UI has already been rebuilt.

## What the screenshot establishes

A persistent left rail contains primary actions, a searchable/recent conversation list, a highlighted selected thread, context menus and a bottom account area. The main pane has a compact conversation header, a wide but readable message column, generous spacing and subdued response actions. A large rounded composer anchors the bottom with attachment/input/send controls. Flat near-black surfaces, light text and restrained separators keep attention on the conversation. Screenshot-specific environment/model controls are not necessary daily OTU navigation. Hidden/obscured areas are not evidence of functionality.

## Recommended OTU adaptation

- Chat is the default screen, with a real New conversation action, searchable/renameable recent threads, platform/opportunity labels, and durable independent conversation identities. Existing per-workspace notes alone are insufficient to claim multiple new chats.
- Main navigation: New conversation, Opportunities, Career library, Connections, Help. Group approval/reply counts under relevant work; account, usage and developer tools remain secondary. Preserve all existing tracking, source verification, approval, revisions and cost controls.
- Main pane: selected conversation title and verified state; readable conversational messages; consistent copy/helpful actions; a sticky composer with a clear Send control. Only show working features—microphone, sharing or attachment features need real supporting behavior before appearing.
- Prepared proposals and documents open in a right-side review panel beside the conversation on larger screens. Include wording changes, visible revisions/version labels, factual review and explicit Save; preserve originals and invalidate changed approvals. On portrait/mobile, use a drawer/sheet or Chat/Document switch instead of three cramped columns. Keep the composer visible above the keyboard with safe-area/dynamic viewport handling.
- Plain language and clear actions. No technical terms, internal prompts, model/provider controls or environment errors dominate daily work. No simulated connection/activity indicators.

## Matrix digital rain

Authentic visual direction: downward columns of changing digits/letters and appropriate supported glyphs; brighter leading characters; fading green trails; varied speeds, trail lengths and gaps on a near-black background. Sparse visible streams should remain recognizable around the workspace. Avoid flashy pulses and dense bright motion behind text. Keep messages, composer, forms and document surfaces dark and sufficiently opaque for stable contrast.

Use a decorative local Canvas layer, ignored by screen readers and pointer events. Schedule with requestAnimationFrame and a deliberately modest frame-rate target (initially 15–20 fps to be tested), cap render resolution/density, handle resizing, stop when hidden and use a lighter mobile mode. The effect makes no inference/API requests, though device rendering still consumes resources. Respect prefers-reduced-motion with a static default for those users and provide a visible animation pause/off control. Save the preference per device. Test iPad Safari, keyboard interaction, focus, small-screen overflow and reading clarity.

## Verified research

Six public authoritative pages were retrieved successfully and excerpts saved in docs/UI_REFERENCE_RESEARCH.json:

- W3C WCAG 2.2 Pause, Stop, Hide: automatically moving content lasting more than five seconds alongside other content needs a pause/stop/hide mechanism unless essential. https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html
- MDN prefers-reduced-motion: detect the device preference for reduced nonessential motion. https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- MDN requestAnimationFrame: use repaint-aligned, timestamp-based scheduling; most browsers pause callbacks in background tabs. https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
- MDN Canvas optimization: avoid repeated drawing work and use requestAnimationFrame; account for display pixel density. https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas
- W3C text contrast: normal text at least4.5:1; large text3:1. Measure actual composited surfaces, not just nominal colors. https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- W3C target size minimum: generally24×24 CSS pixels or specified spacing exceptions; recommend approximately44-pixel everyday touch controls for this iPad-oriented app. https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html

These sources support implementation/accessibility decisions. The screenshot itself is the layout reference; no inaccessible product internals, proprietary assets or direct private ChatGPT integration are assumed.
