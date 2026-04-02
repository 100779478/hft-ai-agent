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

