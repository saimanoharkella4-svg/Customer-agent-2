# Data Erasure Runbook (Right to Erasure)

## Regulatory Basis
Under India DPDP 2023 Section 12(1) and GDPR Article 17, data principals have the **right to erasure** of their personal data processed by the TechMart Support Agent.

## Request Intake and Verification
1. Customers may exercise their **right to erasure** via:
   - Self-service portal: Privacy Dashboard > Request Data Erasure.
   - Email: privacy@techmart.com.
2. The Data Protection Officer (DPO) verifies the customer's identity within 24 hours of receiving the request.

## Erasure Execution Procedure
Once verified, the following erasure steps occur within 72 hours:
1. **Active Memory**: Purge active session records and memory caches keyed by the customer's session or customer ID.
2. **Conversation History**: Execute selective data erasure across operational and diagnostic logs:
   `python -m scripts.execute_erasure --customer-id <CUSTOMER_ID>`
3. **Audit Confirmation**: Record the erasure execution in the immutable compliance ledger (logging only the pseudonymized identifier and completion timestamp).
4. **Notice of Erasure**: Confirm completion to the customer via secure communication.
