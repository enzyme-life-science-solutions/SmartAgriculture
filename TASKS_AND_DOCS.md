<!-- what: unify documentation-task lifecycle guidance | why: ensure single compliant entrypoint for agents and developers | standard: IEC 62304 §5.6, ISO 13485, ISO 14971, ISO/IEC 27001, ISO/IEC 27701, HIPAA -->
# Task & Documentation Lifecycle Guide
**Banner:** Research use only. Not for diagnostic or clinical decision-making.

This guide explains how documentation in `docs/PROJECT_DOCS.md` connects to operational queues in `.ops/` and how agents must maintain synchronization using `scripts/extract_tasks_from_docs.py`.

## Lifecycle Overview
1. **Authoring (docs/PROJECT_DOCS.md)**  
   - Tasks live as Markdown checkboxes under sections labeled with `DocID`.
   - Status line (`Status: ☐ Open | ☑ Closed`) indicates readiness; closing occurs automatically when all tasks complete.
2. **Extraction (scripts/extract_tasks_from_docs.py)**  
   - Parse sections, generate/refresh `.ops/queues/PD-XXXX.json`, and update `.ops/agent_handoff_queue.json`.
   - Enforces the compliance banner and maintains audit timestamps, preventing drift (ISO/IEC 27001 integrity).
3. **Execution ( .ops/queues/ )**  
   - Agents lock and advance tasks via queue files; statuses support `pending | in_progress | done | rejected`.
   - Human approval defaults to `approved` to satisfy ISO 14971 risk acknowledgement.
4. **Back-Propagation (docs/PROJECT_DOCS.md)**  
   - When queue tasks reach `done`, the extractor toggles the corresponding checkbox and section status.
   - Footer metadata (`Extracted`, `Last Sync`) logs synchronization (IEC 62304 traceability).

## Operating Procedure
1. Update or add tasks solely in `docs/PROJECT_DOCS.md`.  
2. Run `python3 scripts/extract_tasks_from_docs.py` after edits and before creating PRs.  
3. Work from the generated queue (`.ops/queues/PD-XXXX.json`), updating `status`, `locked_by`, and `audit` as tasks progress.  
4. Re-run the extractor to propagate completions back into the documentation.  
5. Reference queue task IDs (text) in PR descriptions for IEC 62304 trace links.

## Compliance & Risk Controls
- **IEC 62304 §5.6:** Maintains requirement→implementation→verification trace by linking DocID sections to queue entries.  
- **ISO 13485:** Treats this document as controlled guidance outlining the procedure.  
- **ISO 14971:** Reduces handoff risk via a single authoritative flow and explicit human acknowledgement defaults.  
- **ISO/IEC 27001 & 27701 / HIPAA:** Banners prevent misinterpretation as clinical guidance; queues contain no PHI/PII.  
- **Auditability:** JSON queue files include `_meta`, `audit`, and timestamped entries for forensic review.

## Verification Checklist
- `docs/PROJECT_DOCS.md` contains up-to-date tasks and extraction footer timestamps.  
- `.ops/queues/PD-XXXX.json` exists for each DocID and mirrors task status.  
- `.ops/agent_handoff_queue.json` lists every active `PD-XXXX` in `subqueues_index`.  
- `scripts/extract_tasks_from_docs.py` runs without errors and prints `[ok] queues synced`.  
- PR descriptions cite relevant DocID/task text to complete trace chains.

## References
- `docs/SOPs/Task_Queues_SOP.md` — procedural details and locking states.  
- `ops/tasks.mapping.json` — DocID → title lookup to detect mismatches.  
- `.ops/queues/README.md` — directory-level expectations for queue artifacts.  
- `AGENTS.md` — broader agent responsibilities and standard operating conventions.
