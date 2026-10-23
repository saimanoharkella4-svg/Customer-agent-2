import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# In-memory approval records
_APPROVALS: Dict[str, Dict[str, Any]] = {}

def request_approval(action: str, details: Dict[str, Any], requested_by: Optional[str] = None) -> Dict[str, Any]:
    """Creates a pending human-in-the-loop approval record for data-changing actions.
    
    Bulk actions are strictly refused rather than queued.
    """
    # Detect bulk actions in details or action
    details_str = str(details).lower()
    if any(bulk_word in details_str for bulk_word in ["all records", "every customer", "all orders", "bulk", "select *", "drop"]):
        return {
            "status": "refused",
            "approval_id": None,
            "action": action,
            "message": "Bulk actions affecting multiple records or customers are strictly prohibited."
        }

    approval_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
    now_utc = datetime.now(timezone.utc).isoformat()

    record = {
        "approval_id": approval_id,
        "action": action,
        "details": details,
        "requested_by": requested_by or "system",
        "requested_at": now_utc,
        "status": "pending_approval",
        "approved_by": None,
        "approved_at": None,
    }
    _APPROVALS[approval_id] = record

    return {
        "status": "pending_approval",
        "approval_id": approval_id,
        "action": action,
        "message": f"Action '{action}' requires human supervisor authorization. Request registered with approval ID {approval_id}."
    }

def confirm_approval(approval_id: str, approver: str) -> Dict[str, Any]:
    """Confirms and logs human authorization for a pending action."""
    record = _APPROVALS.get(approval_id)
    if not record:
        return {"status": "not_found", "message": f"No approval request found for ID {approval_id}"}
    
    record["status"] = "approved"
    record["approved_by"] = approver
    record["approved_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "approved", "approval_id": approval_id, "approved_by": approver}
