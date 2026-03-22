import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import models
from database import Base
from services.document_extraction import extract_document_content
from services.merge_service import MergeService

# Setup in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestPhase4(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.company = models.Company(name="Test Co", stage="seed")
        self.db.add(self.company)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    @patch("config.settings.get_llm")
    def test_document_ai_extraction(self, mock_get_llm):
        # Mock LLM response
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content='{"merchant_name": "CloudNine", "date": "2025-03-22", "total_amount": 1500.50, "currency": "USD", "category": "Software"}')

        raw_content = b"CloudNine Receipt\nTotal: $1500.50\nDate: 22-03-2025"
        ocr, raw_data, ai_data, status = extract_document_content(raw_content, "receipt.txt", "text/plain")

        self.assertEqual(status, "processed")
        self.assertEqual(ai_data["merchant_name"], "CloudNine")
        self.assertEqual(ai_data["total_amount"], 1500.50)
        self.assertEqual(ai_data["category"], "Software")

    @patch("integrations.merge_client.MergeAccountingClient._request")
    def test_merge_gl_sync(self, mock_request):
        # Mock Merge API responses
        mock_request.side_effect = [
            {"results": [{"id": "acc_1", "name": "Cash", "classification": "ASSET", "type": "BANK"}]}, # accounts
            {"results": [{"id": "je_1", "transaction_date": "2025-03-20", "memo": "Monthly Rent", "lines": [{"net_amount": -2000, "account": {"id": "acc_1", "name": "Cash"}}]}]}, # journal entries
            {"results": []} # invoices
        ]

        service = MergeService(self.db, self.company.id)
        result = service.sync_all()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["stats"]["accounts"], 1)
        self.assertEqual(result["stats"]["gl_entries"], 1)

        # Verify GL entry in DB
        gl_entry = self.db.query(models.GeneralLedger).filter(models.GeneralLedger.reference_id == "je_1").first()
        self.assertIsNotNone(gl_entry)
        self.assertEqual(gl_entry.credit_amount, 2000)
        self.assertEqual(gl_entry.description, "Monthly Rent")

if __name__ == "__main__":
    unittest.main()
