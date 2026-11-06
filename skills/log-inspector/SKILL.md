---
name: log-inspector
description: Analyzes service error logs, filters high-frequency stack traces, and recommends immediate mitigation steps. Use when the user asks to debug errors or inspect application logs.
---

# Log Inspection Workflow

Follow this procedure when triaging log dumps:

1. **Scan and Filter**:
   - Use the `run_command` tool to execute `python scripts/filter_errors.py --path <log_file>`.
2. **Consult Runbooks**:
   - For database timeouts, refer to `references/db_runbook.md`.
3. **Output Format**:
   - Summarize root causes by occurrence frequency.
   - Propose an explicit remediation plan.
