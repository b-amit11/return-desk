"""Opt-in HubSpot CRM ticket integration for human-reviewed return cases."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class TicketClient(Protocol):
    def create_ticket(self, properties: dict[str, str]) -> dict: ...


class HubSpotError(RuntimeError):
    """Raised when HubSpot rejects a ticket request or is unavailable."""


@dataclass
class HubSpotTicketClient:
    """Minimal HubSpot Tickets API client using a sandbox private-app token."""

    token: str
    base_url: str = "https://api.hubapi.com"

    @classmethod
    def from_environment(cls) -> "HubSpotTicketClient":
        token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
        if not token:
            raise HubSpotError("Set HUBSPOT_PRIVATE_APP_TOKEN in .env to enable HubSpot submission.")
        return cls(token=token)

    def create_ticket(self, properties: dict[str, str]) -> dict:
        body = json.dumps({"properties": properties}).encode("utf-8")
        request = Request(
            f"{self.base_url}/crm/v3/objects/tickets",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise HubSpotError(f"HubSpot rejected the ticket request ({exc.code}): {detail}") from exc
        except URLError as exc:
            raise HubSpotError("Could not reach HubSpot; no ticket was created.") from exc


def build_ticket_properties(result: dict) -> dict[str, str]:
    """Create a bounded, auditable CRM payload; customer text is never forwarded."""
    decision = result["decision"]
    intake = result["intake"]
    order = result.get("order") or {}
    if decision["status"] not in {"eligible", "human_review"}:
        raise ValueError("Only cases requiring an agent decision can be submitted to CRM.")
    citations = ", ".join(decision["citations"])
    content = "\n".join(
        [
            "ReturnDesk human-review queue item (synthetic demo data).",
            f"Decision: {decision['status']}",
            f"Order: {intake.get('order_id') or 'unverified'}",
            f"Item: {order.get('item', 'unverified')}",
            f"Reason: {intake.get('reason', 'unknown')}",
            f"Condition: {intake.get('condition', 'unknown')}",
            f"Policy citations: {citations}",
            f"Explanation: {decision['explanation']}",
            "Human approval is required. No refund has been issued.",
        ]
    )
    return {
        "hs_ticket_subject": f"Return review: {intake.get('order_id') or 'unverified order'}",
        "hs_ticket_priority": "HIGH" if decision["status"] == "human_review" else "MEDIUM",
        "content": content,
    }


def submit_for_human_review(result: dict, client: TicketClient) -> dict:
    """Submit exactly one approved review payload through the supplied ticket client."""
    created = client.create_ticket(build_ticket_properties(result))
    return {"ticket_id": created.get("id"), "properties": build_ticket_properties(result)}
