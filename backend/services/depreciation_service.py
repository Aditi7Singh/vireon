"""
Depreciation Service
====================
Business logic for automated depreciation GL posting and asset disposal.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

import models


def post_depreciation_to_gl(db: Session, company_id: UUID, target_month: date) -> Dict[str, Any]:
    """
    Compute monthly depreciation for all active assets and post
    double-entry GL records (Debit Depreciation Expense / Credit Accumulated Depreciation).

    Returns summary of entries posted.
    """
    start_of_month = target_month.replace(day=1)
    if start_of_month.month == 12:
        end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)

    # Check if already posted for this month
    existing = db.query(models.GeneralLedger).filter(
        models.GeneralLedger.company_id == company_id,
        models.GeneralLedger.account_code == models.GLAccountCode.DEPRECIATION_EXPENSE,
        models.GeneralLedger.source_type == "depreciation_auto",
        models.GeneralLedger.transaction_date >= start_of_month,
        models.GeneralLedger.transaction_date <= end_of_month,
    ).first()
    if existing:
        return {"status": "already_posted", "month": str(start_of_month)}

    active_assets = db.query(models.FixedAsset).filter(
        models.FixedAsset.company_id == company_id,
        models.FixedAsset.status == "active",
        models.FixedAsset.purchase_date <= end_of_month,
    ).all()

    entries_posted = 0
    total_depreciation = Decimal("0")

    for asset in active_assets:
        cost = Decimal(str(asset.purchase_cost))
        salvage = Decimal(str(asset.salvage_value or 0))
        useful_months = asset.useful_life_years * 12
        if useful_months <= 0:
            continue

        # Calculate monthly depreciation
        if asset.depreciation_method == "declining_balance":
            # Double declining balance
            annual_rate = Decimal("2") / Decimal(str(asset.useful_life_years))
            book_val = cost - Decimal(str(asset.accumulated_depreciation or 0))
            monthly_dep = (book_val * annual_rate) / Decimal("12")
            if book_val - monthly_dep < salvage:
                monthly_dep = book_val - salvage
        else:
            # Straight line (default)
            depreciable = cost - salvage
            monthly_dep = depreciable / Decimal(str(useful_months))

        if monthly_dep <= 0:
            continue

        monthly_dep = round(monthly_dep, 2)
        total_depreciation += monthly_dep

        # Update asset accumulated depreciation and book value
        new_accum = Decimal(str(asset.accumulated_depreciation or 0)) + monthly_dep
        new_book = cost - new_accum
        asset.accumulated_depreciation = new_accum
        asset.book_value = new_book

        if new_book <= salvage:
            asset.status = "fully_depreciated"

        # Create DepreciationEntry record
        dep_entry = models.DepreciationEntry(
            asset_id=asset.id,
            depreciation_date=end_of_month,
            depreciation_amount=monthly_dep,
            accumulated_depreciation=new_accum,
            book_value=new_book,
        )
        db.add(dep_entry)

        # Post GL: Debit Depreciation Expense
        gl_debit = models.GeneralLedger(
            company_id=company_id,
            account_code=models.GLAccountCode.DEPRECIATION_EXPENSE,
            account_name="Depreciation Expense",
            transaction_date=end_of_month,
            debit_amount=monthly_dep,
            credit_amount=Decimal("0"),
            description=f"Monthly depreciation – {asset.asset_name}",
            source_type="depreciation_auto",
            reference_id=str(asset.id),
        )
        db.add(gl_debit)

        # Post GL: Credit Accumulated Depreciation
        gl_credit = models.GeneralLedger(
            company_id=company_id,
            account_code=models.GLAccountCode.ACCUMULATED_DEPRECIATION,
            account_name="Accumulated Depreciation",
            transaction_date=end_of_month,
            debit_amount=Decimal("0"),
            credit_amount=monthly_dep,
            description=f"Monthly depreciation – {asset.asset_name}",
            source_type="depreciation_auto",
            reference_id=str(asset.id),
        )
        db.add(gl_credit)

        entries_posted += 1

    db.commit()

    return {
        "status": "posted",
        "month": str(start_of_month),
        "assets_processed": entries_posted,
        "total_depreciation": float(total_depreciation),
    }


def dispose_asset(db: Session, asset_id: UUID, disposal_value: float, disposal_date: date = None) -> Dict[str, Any]:
    """
    Dispose of a fixed asset and record gain/loss.
    """
    asset = db.query(models.FixedAsset).filter(models.FixedAsset.id == asset_id).first()
    if not asset:
        return {"error": "Asset not found"}

    if asset.status == "disposed":
        return {"error": "Asset already disposed"}

    if not disposal_date:
        disposal_date = date.today()

    book_value = float(asset.book_value or (float(asset.purchase_cost) - float(asset.accumulated_depreciation or 0)))
    gain_loss = disposal_value - book_value

    # Update asset
    asset.status = "disposed"
    asset.disposal_date = disposal_date
    asset.disposal_value = Decimal(str(disposal_value))

    # Post GL entries for disposal
    # Debit Cash/AR for disposal proceeds
    if disposal_value > 0:
        gl_cash = models.GeneralLedger(
            company_id=asset.company_id,
            account_code=models.GLAccountCode.CASH,
            account_name="Cash – Disposal Proceeds",
            transaction_date=disposal_date,
            debit_amount=Decimal(str(disposal_value)),
            credit_amount=Decimal("0"),
            description=f"Disposal proceeds – {asset.asset_name}",
            source_type="asset_disposal",
            reference_id=str(asset.id),
        )
        db.add(gl_cash)

    # Debit Accumulated Depreciation (remove it)
    gl_accum = models.GeneralLedger(
        company_id=asset.company_id,
        account_code=models.GLAccountCode.ACCUMULATED_DEPRECIATION,
        account_name="Accumulated Depreciation",
        transaction_date=disposal_date,
        debit_amount=Decimal(str(asset.accumulated_depreciation or 0)),
        credit_amount=Decimal("0"),
        description=f"Remove accumulated depreciation – {asset.asset_name}",
        source_type="asset_disposal",
        reference_id=str(asset.id),
    )
    db.add(gl_accum)

    # Credit Equipment (original cost)
    gl_equip = models.GeneralLedger(
        company_id=asset.company_id,
        account_code=models.GLAccountCode.EQUIPMENT,
        account_name="Equipment",
        transaction_date=disposal_date,
        debit_amount=Decimal("0"),
        credit_amount=Decimal(str(asset.purchase_cost)),
        description=f"Remove asset cost – {asset.asset_name}",
        source_type="asset_disposal",
        reference_id=str(asset.id),
    )
    db.add(gl_equip)

    # Gain or Loss
    if gain_loss > 0:
        # Credit gain
        gl_gain = models.GeneralLedger(
            company_id=asset.company_id,
            account_code=models.GLAccountCode.PRODUCT_REVENUE,  # Use a revenue code for gain
            account_name="Gain on Disposal of Asset",
            transaction_date=disposal_date,
            debit_amount=Decimal("0"),
            credit_amount=Decimal(str(abs(gain_loss))),
            description=f"Gain on disposal – {asset.asset_name}",
            source_type="asset_disposal",
            reference_id=str(asset.id),
        )
        db.add(gl_gain)
    elif gain_loss < 0:
        # Debit loss
        gl_loss = models.GeneralLedger(
            company_id=asset.company_id,
            account_code=models.GLAccountCode.DEPRECIATION_EXPENSE,  # Use expense code for loss
            account_name="Loss on Disposal of Asset",
            transaction_date=disposal_date,
            debit_amount=Decimal(str(abs(gain_loss))),
            credit_amount=Decimal("0"),
            description=f"Loss on disposal – {asset.asset_name}",
            source_type="asset_disposal",
            reference_id=str(asset.id),
        )
        db.add(gl_loss)

    db.commit()

    return {
        "asset_id": str(asset.id),
        "asset_name": asset.asset_name,
        "disposal_date": str(disposal_date),
        "disposal_value": disposal_value,
        "book_value_at_disposal": book_value,
        "gain_loss": round(gain_loss, 2),
        "gain_loss_type": "gain" if gain_loss >= 0 else "loss",
        "status": "disposed",
    }
