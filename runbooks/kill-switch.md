# Kill-Switch Runbook

## Overview
This runbook provides step-by-step instructions to immediately stop the entire agent service or disable a single tool (such as `create_refund`) within 5 minutes.

## Procedure 1: Stop a Single Tool Within 5 Minutes
If a specific tool (e.g. `create_refund`) exhibits anomalous behavior or security risk:
1. Set the tool disable environment variable:
   - For `create_refund`: Set `DISABLE_TOOL_CREATE_REFUND=true`
   - For `search_orders`: Set `DISABLE_TOOL_SEARCH_ORDERS=true`
2. Alternatively, revoke tool approval credentials in the supervisor dashboard.
3. The change takes effect dynamically within 30 seconds without restarting the service. Any subsequent calls return:
   `{"status": "disabled", "message": "This capability is temporarily disabled by administrative policy."}`

## Procedure 2: Complete Agent Emergency Stop (< 2 Minutes)
To shut down the entire agent service immediately:
1. **Container / Orchestrator Level**:
   - Kubernetes: `kubectl scale deployment support-agent --replicas=0`
   - Docker / Cloud Run: Set container traffic to 0 or execute `docker stop support_agent`
2. **Reverse Proxy / CDN Level**:
   - Set routing rule on AWS CloudFront / Cloudflare to return HTTP 503 for all requests matching `/chat`.
3. **Verify Cessation**:
   - Send probe to `GET /health` and `POST /chat` to confirm requests are halted.
4. **Log Incident**:
   - Inform the security team per `runbooks/incident-response.md`.
