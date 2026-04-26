from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict, Iterable

import httpx


def fetch_live_inr_rates(currencies: Iterable[str]) -> Dict[str, Decimal]:
    """Fetch live FX rates and normalize as BASE->INR rates.

    Uses exchangerate.host public endpoint and returns a map such as:
    {"USD": Decimal("83.12"), "EUR": Decimal("90.55")}
    """
    normalized = []
    for c in currencies:
        code = (c or "").upper().strip()
        if code and code != "INR":
            normalized.append(code)

    rates: Dict[str, Decimal] = {"INR": Decimal("1")}
    for code in normalized:
        # Request INR quote for each base currency so we can persist BASE->INR directly.
        url = "https://api.exchangerate.host/latest"
        response = httpx.get(url, params={"base": code, "symbols": "INR"}, timeout=10)
        response.raise_for_status()
        payload = response.json()
        inr_rate = payload.get("rates", {}).get("INR")
        if inr_rate is None:
            raise RuntimeError(f"Missing INR rate for {code}")
        rates[code] = Decimal(str(inr_rate))

    return rates


def upsert_rates_for_today(db, rates: Dict[str, Decimal]) -> int:
    from uuid import uuid4
    import models

    today = date.today()
    upserted = 0
    for base_currency, rate in rates.items():
        existing = (
            db.query(models.ExchangeRate)
            .filter(
                models.ExchangeRate.base_currency == base_currency,
                models.ExchangeRate.target_currency == "INR",
                models.ExchangeRate.effective_date == today,
            )
            .first()
        )
        if existing:
            existing.exchange_rate = rate
            existing.status = "active"
        else:
            db.add(
                models.ExchangeRate(
                    id=uuid4(),
                    base_currency=base_currency,
                    target_currency="INR",
                    exchange_rate=rate,
                    effective_date=today,
                    status="active",
                )
            )
        upserted += 1

    db.commit()
    return upserted
