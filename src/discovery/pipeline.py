"""Discovery orchestration: iterate every region x segment combination,
search, extract contact info, and hand raw candidates to enrichment.

Iterating region x segment (rather than one broad search) is a deliberate
choice: a single wide search exhausts its useful result pages quickly and
yield collapses. Splitting the search space keeps each individual query
narrow enough that the provider keeps returning genuinely new businesses
across a run instead of the same handful repeatedly.
"""
from __future__ import annotations

from src.config import Settings
from src.discovery.contact_extractor import extract_contact_email
from src.integrations.places_client import PlacesClient
from src.models import Contact, Lead


def run_discovery(
    settings: Settings,
    places_client: PlacesClient,
    website_html_by_url: dict[str, str],
) -> list[Contact]:
    contacts: list[Contact] = []

    for region in settings.regions:
        for segment in settings.segments:
            for term in segment.search_terms:
                results = places_client.search(term, region.key, settings.max_pages_per_search)
                for result in results:
                    lead = Lead(
                        business_name=result["name"],
                        website=result.get("website"),
                        segment_key=segment.key,
                        region_key=region.key,
                    )
                    email, method = None, "none"
                    if lead.website and lead.website in website_html_by_url:
                        email, method = extract_contact_email(
                            lead.website, website_html_by_url[lead.website]
                        )
                    contacts.append(
                        Contact(
                            lead=lead,
                            email=email,
                            phone=result.get("phone"),
                            extraction_method=method,
                        )
                    )
    return contacts
