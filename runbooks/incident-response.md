# Incident Response Runbook

## Scope and Classification
This runbook guides operational and engineering teams when handling security incidents, critical service outages, prompt injection breakthroughs, or data integrity breaches affecting the Support Agent.

## Escalation and Alerting: Who is Alerted
1. **P1 / Critical Incidents** (data breach, remote code injection, widespread outage):
   - On-Call Security Engineer (PagerDuty / phone alert immediately)
   - Lead System Architect
   - Data Protection Officer (DPO)
   - VP of Customer Engineering
2. **P2 / High Incidents** (degraded latency > 8000ms, tool errors):
   - Operations on-call engineer via Slack #agent-ops channel

## First Steps (Immediate Triage)
1. **Activate Kill Switch**: If active compromise, prompt injection loop, or data leak is detected, trigger the kill switch immediately:
   `AGENT_ENABLED=false` or isolate the instance.
2. **Isolate Logs and Traces**: Extract the `trace_id` of the triggering requests to isolate affected session memories and IP addresses.
3. **Capture Memory Snapshot**: Record volatile in-memory state for forensic root cause analysis before terminating the container.
4. **Deploy Rollback / Hotfix**: If introduced by recent deployment, initiate immediate rollback per `runbooks/rollback.md`.

## User Communication: How Users are Told
1. **Service Banner**: If the service is suspended, the `/chat` route returns a standardized maintenance response:
   `{"detail": "Support service temporarily undergoing maintenance. Please reach out to support@techmart.com."}`
2. **Direct Notification**: If customer data was accessed or impacted, the DPO coordinates formal notification within 72 hours via email:
   - Nature of the incident
   - Personal data categories involved
   - Mitigating actions taken
   - Contact point for assistance
