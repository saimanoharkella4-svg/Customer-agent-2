# Secret Rotation Runbook

## Overview
This runbook describes the procedure to rotate `AGENT_API_TOKEN` and the language model API key (`GROQ_API_KEY`) without service disruption. Secrets must be rotated at least every 90 days, or immediately upon detection of potential exposure.

## Rotating AGENT_API_TOKEN
1. **Generate New Secret**:
   Generate a high-entropy cryptographically secure token:
   `openssl rand -hex 32`
2. **Update Agent Environments**:
   Update `AGENT_API_TOKEN` in the environment configuration of both Sandbox and Production deployments.
3. **Update CertifyAI Server Configuration**:
   Update the corresponding `SUPPORT_AGENT_TOKEN` secret in the CertifyAI test management settings.
4. **Update Authorized Clients**:
   Update frontend clients and integrations with the new bearer token.
5. **Verify Access**:
   Send an authenticated test request to `POST /chat`. Verify HTTP 200 response. Send request with old token to confirm rejection with HTTP 403.

## Rotating Model API Key (GROQ_API_KEY)
1. **Generate New Key in Provider Console**:
   Log in to the Groq Cloud Console and create a new API key labeled `support-agent-prod-<DATE>`.
2. **Deploy New Environment Variable**:
   Set `GROQ_API_KEY` in the hosting environment secrets manager.
3. **Trigger Rolling Restart**:
   Perform a zero-downtime rolling restart of the agent instances.
4. **Validate LLM Functionality**:
   Verify conversational responses are completing normally and cost calculations remain accurate.
5. **Revoke Old Key**:
   Delete or deactivate the deprecated API key in the Groq Cloud Console.
