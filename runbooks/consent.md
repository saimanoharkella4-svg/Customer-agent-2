# Consent Management Runbook

## Overview
This runbook defines how customer consent is captured, verified, and logged for the TechMart Support Agent under India DPDP 2023 regulations and global privacy frameworks.

## Consent Notice and Presentation
1. **Notice on Connection**: When a customer initiates a session, a prominent notice is presented:
   *"You are interacting with the TechMart Automated Support Agent. To assist with orders and refunds, we process your name, contact details, and order history with your explicit consent."*
2. **Explicit Affirmative Action**: The user must acknowledge the consent banner before personal identifiers are retrieved or processed.
3. **Withdrawal of Consent**: Users may withdraw consent at any time by typing "withdraw consent" or by submitting a request to privacy@techmart.com.

## Consent Logging
- Every granted consent event is recorded with:
  - User Identifier / Session ID
  - Timestamp (UTC)
  - Consent scope (order inquiry, refund processing)
  - Notice version ID
- Consent records are securely stored in the audit database and retained alongside session records.
