# Data Retention Runbook

## Retention Schedules
All customer interactions, session memory, and associated personal data processed by the Support Agent are governed by strict retention periods under DPDP S.8(7) regulations:

1. **In-Memory Session Data**:
   - In-memory conversation state has a strict TTL of 30 minutes (1,800 seconds).
   - Once the TTL expires, the session entries automatically delete from active memory.

2. **Audit and Request Logs**:
   - Application audit logs retain records for exactly 30 days to support customer service traceability.
   - Automated batch purge scripts execute daily to delete all log entries older than 30 days.

3. **Approval Records**:
   - Human-in-the-loop approval records retain data for 90 days for financial compliance.
   - After 90 days, automated jobs delete all non-essential metadata.

## Deletion and Purge Procedures
- Administrators can trigger an immediate automated purge with the retention CLI:
  `python -m scripts.purge_retention --older-than 30d`
- Verifies that all targeted records delete completely across memory caches and persistent storage.
