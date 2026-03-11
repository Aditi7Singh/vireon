"""
Vendor and Customer contact generator.
FIX: Populate company field on every Contact.
"""

from data_generation.config import VENDORS, CUSTOMERS
from data_generation.models import Contact, ContactStatus, Address, AddressType, PhoneNumber
import random


def _random_phone() -> str:
    return f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"


def _random_address() -> Address:
    streets = [
        "100 Market St", "250 Broadway", "500 Tech Park Dr",
        "1200 Innovation Way", "75 Startup Blvd", "300 Enterprise Ave",
        "88 Silicon Ct", "420 Commerce Rd", "15 Harbor View",
        "900 Capital Heights Pkwy",
    ]
    cities = [
        ("San Francisco", "CA", "94105"),
        ("New York",      "NY", "10013"),
        ("Austin",        "TX", "78701"),
        ("Seattle",       "WA", "98101"),
        ("Denver",        "CO", "80202"),
        ("Boston",        "MA", "02101"),
        ("Chicago",       "IL", "60601"),
        ("Los Angeles",   "CA", "90012"),
    ]
    street = random.choice(streets)
    city, state, zipcode = random.choice(cities)
    return Address(
        type=AddressType.BILLING,
        street_1=street,
        city=city,
        state=state,
        country="US",
        zip_code=zipcode,
    )


def generate_contacts(company_id: str = None, seed: int = 42) -> dict:
    """
    Generate vendor and customer contacts.
    FIX: company_id is now passed in and applied to every Contact.

    Returns dict with keys 'vendors', 'customers', 'all'.
    """
    random.seed(seed)

    vendor_map   = {}
    customer_map = {}
    all_contacts = []

    # ── Vendors (is_supplier=True) ──
    for v in VENDORS:
        contact = Contact(
            name=v["name"],
            is_supplier=True,
            is_customer=False,
            email_address=v.get("email"),
            status=ContactStatus.ACTIVE,
            company=company_id,          # FIX: was always None
            addresses=[_random_address()],
            phone_numbers=[PhoneNumber(number=_random_phone())],
        )
        vendor_map[v["name"]] = contact
        all_contacts.append(contact)

    # ── Customers (is_customer=True) ──
    for c in CUSTOMERS:
        domain = c["name"].lower().replace(" ", "").replace(".", "").replace(",", "")
        contact = Contact(
            name=c["name"],
            is_supplier=False,
            is_customer=True,
            email_address=f"accounts@{domain}.com",
            status=ContactStatus.ACTIVE,
            company=company_id,          # FIX: was always None
            addresses=[_random_address()],
            phone_numbers=[PhoneNumber(number=_random_phone())],
        )
        customer_map[c["name"]] = contact
        all_contacts.append(contact)

    return {
        "vendors":   vendor_map,
        "customers": customer_map,
        "all":       all_contacts,
    }
