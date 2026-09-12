from src.approval.approval_flow import poll_approval, request_approval
from src.integrations.slack_client import MockSlackClient
from src.models import ApprovalState, Draft
from src.state.store import StateStore

CHANNEL = "#outreach-approvals"


def _draft() -> Draft:
    return Draft(
        contact_email="a@example.com",
        subject="Subject",
        body="Body",
        template_key="segment_a",
        generated_by="template",
        stage_label="initial",
    )


def test_approval_flips_state_to_approved(tmp_path):
    slack = MockSlackClient()
    state = StateStore(path=str(tmp_path / "state.json"))
    req = request_approval(_draft(), slack, CHANNEL)
    slack.simulate_reaction(req.message_id, "approved")  # type: ignore[attr-defined]
    req = poll_approval(req, slack, CHANNEL, state)
    assert req.state == ApprovalState.APPROVED
    assert state.is_halted("a@example.com") is False


def test_rejection_halts_the_contact(tmp_path):
    slack = MockSlackClient()
    state = StateStore(path=str(tmp_path / "state.json"))
    req = request_approval(_draft(), slack, CHANNEL)
    slack.simulate_reaction(req.message_id, "rejected")  # type: ignore[attr-defined]
    req = poll_approval(req, slack, CHANNEL, state)
    assert req.state == ApprovalState.REJECTED
    assert state.is_halted("a@example.com") is True


def test_no_reaction_yet_leaves_request_pending(tmp_path):
    slack = MockSlackClient()
    state = StateStore(path=str(tmp_path / "state.json"))
    req = request_approval(_draft(), slack, CHANNEL)
    req = poll_approval(req, slack, CHANNEL, state)
    assert req.state == ApprovalState.PENDING
