from src.enrichment.dedup import dedup_contacts
from src.models import Contact, Lead
from src.state.store import StateStore


def _contact(email: str) -> Contact:
    return Contact(
        lead=Lead(business_name=email, website=None, segment_key="segment_a", region_key="region_1"),
        email=email,
        phone=None,
        extraction_method="mailto",
    )


def test_known_crm_email_is_dropped(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    contacts = [_contact("known@example.com"), _contact("new@example.com")]
    result = dedup_contacts(contacts, known_crm_emails={"known@example.com"}, state=state)
    assert [c.email for c in result] == ["new@example.com"]


def test_duplicate_within_same_run_is_dropped(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    contacts = [_contact("dup@example.com"), _contact("dup@example.com")]
    result = dedup_contacts(contacts, known_crm_emails=set(), state=state)
    assert len(result) == 1


def test_already_in_local_state_is_dropped(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    state.upsert_contact("existing@example.com", {"stage": "sent"})
    contacts = [_contact("existing@example.com"), _contact("new@example.com")]
    result = dedup_contacts(contacts, known_crm_emails=set(), state=state)
    assert [c.email for c in result] == ["new@example.com"]


def test_contacts_without_email_are_dropped(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    contact = Contact(
        lead=Lead(business_name="No Email Co", website=None, segment_key="segment_a", region_key="region_1"),
        email=None,
        phone=None,
        extraction_method="none",
    )
    result = dedup_contacts([contact], known_crm_emails=set(), state=state)
    assert result == []
