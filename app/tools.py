import csv
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.config import DATASET_DIR
from app.approvals import request_approval

def tool(fn):
    """Decorator to mark and register agent tool functions."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    wrapper.is_tool = True
    return wrapper

def _load_orders() -> List[Dict[str, str]]:
    orders_csv = DATASET_DIR / "orders.csv"
    if not orders_csv.exists():
        return []
    with open(orders_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _load_products() -> List[Dict[str, str]]:
    products_csv = DATASET_DIR / "products.csv"
    if not products_csv.exists():
        return []
    with open(products_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

class SearchOrdersInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="Order ID, product name, or status to query")
    customer_id: Optional[str] = Field(None, description="Optional customer ID to scope order search")

@tool
def search_orders(query: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
    """Searches order records by order ID, product name, or status. Customers see only their own data."""
    orders = _load_orders()
    query_clean = query.strip().lower()
    matches = []

    for order in orders:
        # Enforce customer boundary: if customer_id provided, filter strictly
        if customer_id and order.get("customer_id") != customer_id:
            continue

        if (query_clean in order.get("order_id", "").lower() or
            query_clean in order.get("product_name", "").lower() or
            query_clean in order.get("status", "").lower()):
            matches.append({
                "order_id": order.get("order_id"),
                "product_name": order.get("product_name"),
                "quantity": int(order.get("quantity", 1)),
                "status": order.get("status"),
                "tracking_id": order.get("tracking_id"),
                "order_date": order.get("order_date"),
            })

    return {
        "count": len(matches),
        "orders": matches,
        "query": query,
        "as_of": datetime.now(timezone.utc).isoformat()
    }

class GetOrderStatusInput(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=50, description="Unique Order ID such as ORD00255")
    customer_id: Optional[str] = Field(None, description="Optional customer ID for access control")

@tool
def get_order_status(order_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves current order status, shipment tracking, and order date for a specific order ID."""
    orders = _load_orders()
    target_id = order_id.strip().upper()

    for order in orders:
        if order.get("order_id", "").upper() == target_id:
            # Check customer isolation if customer_id supplied
            if customer_id and order.get("customer_id") != customer_id:
                return {
                    "error": "Order not found or access denied.",
                    "order_id": target_id,
                    "found": False
                }

            return {
                "order_id": order.get("order_id"),
                "status": order.get("status"),
                "tracking_id": order.get("tracking_id"),
                "order_date": order.get("order_date"),
                "product_name": order.get("product_name"),
                "quantity": int(order.get("quantity", 1)),
                "found": True,
                "as_of": datetime.now(timezone.utc).isoformat()
            }

    return {
        "error": "Order not found in customer records.",
        "order_id": target_id,
        "found": False,
        "as_of": datetime.now(timezone.utc).isoformat()
    }

class CreateRefundInput(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=50, description="Order ID to request refund for")
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for refund")
    amount_usd: float = Field(..., gt=0.0, description="Refund amount in USD, non-negative")
    customer_id: Optional[str] = Field(None, description="Customer ID requesting refund")

@tool
def create_refund(order_id: str, reason: str, amount_usd: float, customer_id: Optional[str] = None) -> Dict[str, Any]:
    """Creates a refund request for an order. Requires human supervisor authorization before execution."""
    clean_order_id = order_id.strip().upper()
    rounded_amount = round(max(0.0, amount_usd), 2)

    # Check bulk request prevention
    if any(bulk_kw in clean_order_id.lower() for bulk_kw in ["all", "every", "*"]):
        return {
            "status": "refused",
            "message": "Bulk refund requests are prohibited."
        }

    # Verify order exists in records
    orders = _load_orders()
    existing_order = next((o for o in orders if o.get("order_id", "").upper() == clean_order_id), None)
    if not existing_order:
        return {
            "status": "rejected",
            "error": f"Cannot create refund. Order {clean_order_id} not found.",
            "order_id": clean_order_id
        }

    # Submit to human-in-the-loop approval system
    approval_result = request_approval(
        action="create_refund",
        details={
            "order_id": clean_order_id,
            "amount_usd": rounded_amount,
            "reason": reason,
            "product_name": existing_order.get("product_name"),
        },
        requested_by=customer_id or existing_order.get("customer_id") or "customer"
    )

    return {
        "status": approval_result.get("status"),
        "approval_id": approval_result.get("approval_id"),
        "order_id": clean_order_id,
        "amount_usd": rounded_amount,
        "reason": reason,
        "message": (
            f"Refund request of ${rounded_amount:.2f} for order {clean_order_id} has been submitted "
            f"and requires supervisor approval (Approval ID: {approval_result.get('approval_id')})."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
