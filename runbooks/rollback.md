# Rollback Runbook

## Overview
This runbook explains how to quickly return the Support Agent to the last known good release in the event of an outage, performance regression, or failed certification check.

## Rollback Procedure
1. **Identify Last Good Release**:
   - Check the GitHub Releases page or git tag history to find the previous certified tag (e.g., `v1.0.0`).
   - Validate that the previous commit passed all CI checks and CertifyAI certification runs.

2. **Trigger Pipeline Rollback**:
   - **GitHub Actions**: Navigate to Actions > Deploy Pipeline > Run Workflow > select the target release tag or commit SHA.
   - **CLI Revert**:
     ```bash
     git checkout <LAST_GOOD_TAG>
     # Or git revert <BAD_COMMIT_SHA> -m 1
     ```

3. **Deploy Identical Commit**:
   - In accordance with deployment rules, deploy the exact same commit to both Sandbox (`SANDBOX_URL`) and Production (`PRODUCTION_URL`).
   - Ensure `openapi.json` and `certify.yaml` match the version of the rolled-back code.

4. **Post-Rollback Verification**:
   - Run health probe: `curl https://<host>/health` (expect `{"status": "ok"}`).
   - Send test inquiry to `/chat` with valid Bearer token.
   - Verify latency and error rates return below SLO thresholds (< 8000ms).
