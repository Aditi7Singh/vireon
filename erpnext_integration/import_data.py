import json
import asyncio
import os
from erpnext_client.client import ERPNextClient
from typing import List, Dict, Any

# Simulation output paths
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DATA_PATH = os.path.join(BASE_PATH, "backend/simulation/output/json")

class ERPNextImporter:
    def __init__(self, client: ERPNextClient):
        self.client = client
        self.contact_map = {} # Maps simulation contact ID to ERPNext name

    def load_json(self, filename: str) -> List[Dict]:
        path = os.path.join(JSON_DATA_PATH, filename)
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get("results", [])

    async def import_contacts(self):
        """
        Import contacts as Customers or Suppliers.
        """
        print("Importing contacts...")
        contacts = self.load_json("contacts.json")
        for contact in contacts:
            is_supplier = any(t == "VENDOR" for t in contact.get("types", []))
            doctype = "Supplier" if is_supplier else "Customer"
            
            data = {
                "customer_name" if not is_supplier else "supplier_name": contact["name"],
                "email_id": contact.get("email"),
                "phone": contact.get("phone"),
                "currency": contact.get("currency", "USD")
            }
            try:
                # Use sync_resource for idempotency
                result = await self.client.sync_resource(
                    doctype, 
                    data, 
                    match_fields=["customer_name" if not is_supplier else "supplier_name"]
                )
                self.contact_map[contact["id"]] = result.get("name") or contact["name"]
            except Exception as e:
                print(f"Error importing {doctype} {contact['name']}: {e}")
                self.contact_map[contact["id"]] = contact["name"]

    async def import_invoices(self):
        """
        Import AR/AP Invoices.
        """
        print("Importing invoices...")
        invoices = self.load_json("invoices.json")
        for inv in invoices:
            is_ar = inv.get("type") == "ACCOUNTS_RECEIVABLE"
            doctype = "Sales Invoice" if is_ar else "Purchase Invoice"
            
            party_field = "customer" if is_ar else "supplier"
            party_name = self.contact_map.get(inv["contact"], "Unknown")
            
            # Map line items
            items = []
            for line in inv.get("line_items", []):
                items.append({
                    "item_name": line["description"],
                    "qty": line["quantity"],
                    "rate": line["unit_price"],
                    "amount": line["total_amount"]
                })

            data = {
                party_field: party_name,
                "posting_date": inv["issue_date"],
                "due_date": inv["due_date"],
                "currency": inv["currency"],
                "items": items,
                "docstatus": 1 if inv["status"] == "PAID" else 0 # 1 means submitted
            }
            
            try:
                # Extract a logical "custom identifier" if existed, otherwise we just create or match by some field
                # For Sales Invoice, let's assume we can match by a combination if needed, but here we just create.
                # If we had an 'external_id' in ERPNext it would be better.
                await self.client.create_doc(doctype, data)
            except Exception as e:
                print(f"Error importing {doctype} {inv['number']}: {e}")

async def main():
    # Placeholder credentials
    client = ERPNextClient(
        base_url=os.getenv("ERPNEXT_URL", "http://localhost:8000"),
        api_key=os.getenv("ERPNEXT_API_KEY", "your_key"),
        api_secret=os.getenv("ERPNEXT_API_SECRET", "your_secret")
    )
    
    importer = ERPNextImporter(client)
    await importer.import_contacts()
    await importer.import_invoices()

if __name__ == "__main__":
    asyncio.run(main())
