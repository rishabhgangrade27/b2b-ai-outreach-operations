from src.enrichment.competitor_filter import filter_competitors
from src.models import Contact, Lead

SUBSTRINGS = ("our own company",)


def _contact(name: str) -> Contact:
    return Contact(
        lead=Lead(business_name=name, website=None, segment_key="segment_a", region_key="region_1"),
        email=f"{name.lower().replace(' ', '')}@example.com",
        phone=None,
        extraction_method="mailto",
    )


def test_competitor_is_filtered_out():
    contacts = [_contact("Our Own Company Pty Ltd"), _contact("Northfield Contracting")]
    result = filter_competitors(contacts, SUBSTRINGS)
    assert [c.lead.business_name for c in result] == ["Northfield Contracting"]


def test_matching_is_case_insensitive():
    contacts = [_contact("OUR OWN COMPANY")]
    result = filter_competitors(contacts, SUBSTRINGS)
    assert result == []


def test_non_matching_names_pass_through():
    contacts = [_contact("Ridgeline Group"), _contact("Harbor Trade Co")]
    result = filter_competitors(contacts, SUBSTRINGS)
    assert len(result) == 2
