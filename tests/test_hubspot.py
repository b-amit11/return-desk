from returndesk.core import workflow
from returndesk.hubspot import build_ticket_properties, submit_for_human_review


class FakeHubSpot:
    def __init__(self): self.calls = []
    def create_ticket(self, properties):
        self.calls.append(properties)
        return {"id": "sandbox-ticket-123"}


def test_evaluation_payload_contains_policy_evidence_and_no_customer_message():
    result = workflow("ORD-1001 damaged")
    payload = build_ticket_properties(result)
    assert payload["hs_ticket_priority"] == "HIGH"
    assert "P2, P5" in payload["content"]
    assert "ORD-1001 damaged" not in payload["content"]
    assert "No refund has been issued" in payload["content"]


def test_ticket_submission_is_explicit_and_uses_one_gateway_call():
    client = FakeHubSpot()
    receipt = submit_for_human_review(workflow("ORD-1001 damaged"), client)
    assert receipt["ticket_id"] == "sandbox-ticket-123"
    assert len(client.calls) == 1


def test_ineligible_and_clarification_cases_are_never_sent():
    import pytest
    with pytest.raises(ValueError): build_ticket_properties(workflow("ORD-1003 changed my mind unopened"))
    with pytest.raises(ValueError): build_ticket_properties(workflow("I need a return"))
