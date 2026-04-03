## [LRN-20260401-001] correction

**Logged**: 2026-04-01T13:50:10.278205+08:00
**Priority**: medium
**Status**: pending
**Area**: frontend

### Summary
Streaming placeholder text in chat UI rendered a literal \n instead of a line break.

### Details
A frontend progress message in `app/chat_playground.html` used `\\n` in the JS source, so the assistant bubble showed the two characters `\n` instead of a newline while stream progress was rendering. Static tests should validate the source-level escaped string and also guard against the accidental double-escaped variant.

### Suggested Action
Prefer source-level assertions for embedded JS strings and add a negative assertion for the double-escaped placeholder form.

### Metadata
- Source: user_feedback
- Related Files: app/chat_playground.html, tests/test_codex_http.py
- Tags: frontend, streaming, escaping, tests


## [LRN-20260403-001] correction

**Logged**: 2026-04-03T00:00:00+08:00
**Priority**: high
**Status**: pending
**Area**: skills

### Summary
Page-generation skills must not skip required interface-document-based confirmation, and generated HFT pages should default to single-screen layouts with internal scroll containers.

### Details
User feedback showed two repeat issues: (1) generation proceeded without confirming missing interface-driven requirements, and (2) generated pages stretched vertically instead of prioritizing a one-screen workbench layout with inner scrolling. Skills should ask only the minimum missing questions derived from `HFT-SDK-接口文档.md`, skip confirmation when the document already provides enough information, and enforce viewport-bounded layouts with `overflow: hidden` on the page shell plus inner scroll areas for dense content.

### Suggested Action
Update orchestration, intake, requirement-confirmation, style, and delivery skills so confirmation is interface-driven and conditional, and add explicit one-screen/internal-scroll layout rules for generated pages.

### Metadata
- Source: user_feedback
- Related Files: .codex/skills/hft-page-orchestrator/SKILL.md, .codex/skills/requirement-intake/SKILL.md, .codex/skills/page_requirement_confirmation/SKILL.md, .codex/skills/reference-html/SKILL.md, .codex/skills/html-artifact-delivery/SKILL.md
- Tags: skills, hft, layout, confirmation

## [LRN-20260403-002] correction

**Logged**: 2026-04-03T00:10:00+08:00
**Priority**: high
**Status**: pending
**Area**: skills

### Summary
Page-generation skills must always perform one interface-document-based second confirmation before generation, even when the request already looks clear.

### Details
User clarified that skipping confirmation entirely is undesirable. The correct behavior is: always perform one friendly second confirmation for page requests, but keep the confirmation narrowly grounded in `HFT-SDK-接口文档.md` and focused on scenario disambiguation such as which report/order/market module the user means. Also avoid exposing internal execution phrasing like writable-environment or file-write constraints in user-facing confirmation messages.

### Suggested Action
Update orchestration and confirmation skills so they always ask one interface-based follow-up before generation, with examples for ambiguous page families like order pages and market pages.

### Metadata
- Source: user_feedback
- Related Files: .codex/skills/hft-page-orchestrator/SKILL.md, .codex/skills/requirement-intake/SKILL.md, .codex/skills/page_requirement_confirmation/SKILL.md
- Tags: skills, confirmation, ux, hft
