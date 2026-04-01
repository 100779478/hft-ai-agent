## [ERR-20260331-001] apply_patch

**Logged**: 2026-03-31T00:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
`apply_patch` failed repeatedly with a Windows sandbox refresh error when targeting files under `app/`.

### Error
```
windows sandbox: setup refresh failed with status exit code: 1
```

### Context
- Operation attempted: `apply_patch` on `app/codex_http.py` and a new HTML file in `app/`
- Environment: Codex desktop, Windows PowerShell, workspace-write sandbox
- Workaround used: controlled `Set-Content` writes for the affected files

### Suggested Fix
Investigate why the patch tool fails to refresh the Windows sandbox for files in this workspace, and document an approved fallback edit path.

### Metadata
- Reproducible: unknown
- Related Files: app/codex_http.py, app/chat_playground.html

---
