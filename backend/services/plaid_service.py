from __future__ import annotations

import os
from datetime import date
from typing import Dict, List, Optional

import httpx


def _plaid_base_url() -> str:
    env = (os.getenv("PLAID_ENV", "sandbox") or "sandbox").lower()
    if env == "production":
        return "https://production.plaid.com"
    if env == "development":
        return "https://development.plaid.com"
    return "https://sandbox.plaid.com"


def _plaid_headers() -> Dict[str, str]:
    return {"Content-Type": "application/json"}


def _plaid_auth_payload() -> Dict[str, str]:
    client_id = os.getenv("PLAID_CLIENT_ID", "")
    secret = os.getenv("PLAID_SECRET", "")
    if not client_id or not secret:
        raise RuntimeError("PLAID_CLIENT_ID/PLAID_SECRET not configured")
    return {"client_id": client_id, "secret": secret}


def create_link_token(company_id: str, user_id: Optional[str] = None) -> Dict:
    payload = {
        **_plaid_auth_payload(),
        "client_name": "Vireon",
        "country_codes": ["US"],
        "language": "en",
        "products": ["transactions"],
        "user": {
            "client_user_id": user_id or f"vireon-{company_id}",
        },
    }

    with httpx.Client(timeout=20) as client:
        response = client.post(f"{_plaid_base_url()}/link/token/create", json=payload, headers=_plaid_headers())
        response.raise_for_status()
        return response.json()


def exchange_public_token(public_token: str) -> Dict:
    payload = {
        **_plaid_auth_payload(),
        "public_token": public_token,
    }
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{_plaid_base_url()}/item/public_token/exchange",
            json=payload,
            headers=_plaid_headers(),
        )
        response.raise_for_status()
        return response.json()


def get_accounts(access_token: str) -> List[Dict]:
    payload = {
        **_plaid_auth_payload(),
        "access_token": access_token,
    }
    with httpx.Client(timeout=20) as client:
        response = client.post(f"{_plaid_base_url()}/accounts/get", json=payload, headers=_plaid_headers())
        response.raise_for_status()
        return response.json().get("accounts", [])


def get_transactions(access_token: str, start_date: date, end_date: date) -> List[Dict]:
    payload = {
        **_plaid_auth_payload(),
        "access_token": access_token,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "options": {
            "count": 500,
            "offset": 0,
        },
    }

    transactions: List[Dict] = []
    total = 0

    with httpx.Client(timeout=30) as client:
        while True:
            response = client.post(f"{_plaid_base_url()}/transactions/get", json=payload, headers=_plaid_headers())
            response.raise_for_status()
            data = response.json()

            batch = data.get("transactions", [])
            transactions.extend(batch)
            total = int(data.get("total_transactions", len(transactions)))

            if len(transactions) >= total:
                break

            payload["options"]["offset"] = len(transactions)

    return transactions
