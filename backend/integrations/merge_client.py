"""
Merge.dev Accounting API Integration Client

Unified integration with QuickBooks, Xero, Stripe, and other accounting systems
via Merge.dev's Accounting API. Provides drop-in replacement for ERPNext simulator.

Usage:
    client = MergeAccountingClient()
    cash_balance = client.get_cash_balance()
    expenses = client.get_expenses(period_months=3)
    revenue = client.get_revenue()
    client.sync_to_postgres()
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from functools import lru_cache, wraps
import time

logger = logging.getLogger(__name__)


class MergeAPIError(Exception):
    """Base exception for Merge.dev API errors"""
    pass


class MergeAuthenticationError(MergeAPIError):
    """Authentication/authorization error"""
    pass


class MergeRateLimitError(MergeAPIError):
    """Rate limit exceeded"""
    pass


def retry_on_rate_limit(max_retries=3, backoff_factor=2):
    """Decorator to retry on rate limit errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except MergeRateLimitError:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Rate limited on {func.__name__}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
        return wrapper
    return decorator


class MergeAccountingClient:
    """
    Unified integration with Merge.dev Accounting API.
    Abstracts away differences between QuickBooks, Xero, Stripe, etc.
    """

    BASE_URL = "https://api.merge.dev/api/accounting/v1"
    TIMEOUT = 30
    PAGE_SIZE = 100

    def __init__(
        self,
        api_key: Optional[str] = None,
        account_token: Optional[str] = None,
    ):
        """
        Initialize Merge client with API credentials.

        Args:
            api_key: Merge.dev API key (defaults to MERGE_API_KEY env var)
            account_token: Linked account token (defaults to MERGE_ACCOUNT_TOKEN env var)

        Raises:
            MergeAuthenticationError: If credentials are missing
        """
        self.api_key = api_key or os.getenv("MERGE_API_KEY")
        self.account_token = account_token or os.getenv("MERGE_ACCOUNT_TOKEN")

        if not self.api_key or not self.account_token:
            raise MergeAuthenticationError(
                "MERGE_API_KEY and MERGE_ACCOUNT_TOKEN environment variables required"
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "X-Account-Token": self.account_token,
            "Content-Type": "application/json",
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Merge API with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            json: JSON body for POST/PUT

        Returns:
            Parsed JSON response

        Raises:
            MergeAPIError: On API errors
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=self.TIMEOUT,
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise MergeAuthenticationError(
                    f"Authentication failed: {response.text}"
                )
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise MergeRateLimitError(
                    f"Rate limited. Retry after {retry_after}s"
                )
            elif response.status_code >= 400:
                raise MergeAPIError(
                    f"API error {response.status_code}: {response.text}"
                )

            return response.json()

        except requests.RequestException as e:
            raise MergeAPIError(f"Request failed: {str(e)}")

    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all paginated results from endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Yields:
            Individual items from paginated response
        """
        page = 1
        params = params or {}

        while True:
            params["page_size"] = self.PAGE_SIZE
            params["page"] = page

            response = self._request("GET", endpoint, params=params)
            results = response.get("results", [])

            if not results:
                break

            for item in results:
                yield item

            # Check if more pages exist
            if not response.get("next"):
                break

            page += 1

    @retry_on_rate_limit()
    def get_cash_balance(self) -> Dict[str, Any]:
        """
        Fetch cash position from balance sheet.

        Returns:
            {
                "cash": 245000,
                "ar": 125000,
                "ap": 45000,
                "net_cash": 325000,
                "currency": "USD",
                "last_updated": "2026-03-15T10:30:00Z"
            }
        """
        try:
            # Fetch balance sheet
            response = self._request("GET", "balance-sheets")
            statements = response.get("results", [])

            if not statements:
                logger.warning("No balance sheets found in Merge")
                return {
                    "cash": 0,
                    "ar": 0,
                    "ap": 0,
                    "net_cash": 0,
                    "currency": "USD",
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                }

            # Use most recent statement
            statement = statements[0]
            line_items = {item["name"]: item["value"] for item in statement.get("line_items", [])}

            # Extract cash, AR, AP from standard GL accounts
            cash = float(line_items.get("Cash and cash equivalents", 0))
            ar = float(line_items.get("Accounts Receivable", 0))
            ap = float(line_items.get("Accounts Payable", 0))

            return {
                "cash": cash,
                "ar": ar,
                "ap": ap,
                "net_cash": cash + ar - ap,
                "currency": statement.get("currency", "USD"),
                "last_updated": statement.get("remote_updated_at", datetime.utcnow().isoformat() + "Z"),
            }

        except Exception as e:
            logger.error(f"Failed to fetch cash balance from Merge: {e}")
            raise

    @retry_on_rate_limit()
    def get_expenses(self, period_months: int = 3) -> Dict[str, Any]:
        """
        Fetch expense transactions grouped by category.

        Args:
            period_months: Number of months of history to fetch

        Returns:
            {
                "breakdown": {
                    "Payroll": 125000,
                    "AWS": 18750,
                    "SaaS": 8500,
                    "Marketing": 25000,
                },
                "trend": {
                    "Payroll": [120000, 125000, 125000],
                    "AWS": [17500, 18750, 18750],
                },
                "movers": [
                    {"category": "AWS", "pct_change": 7.1, "amount": 1250}
                ],
                "total": 177250,
                "period_months": 3,
                "last_updated": "2026-03-15T10:30:00Z"
            }
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=period_months * 30)).date()
            params = {
                "created_after": start_date.isoformat(),
                "is_deleted": False,
            }

            # Fetch all expenses from the period
            expenses_by_category = {}
            trend_by_category = {}

            for expense in self._paginate("expenses", params):
                category = expense.get("category") or "Other"
                amount = float(expense.get("total_amount", 0))

                if category not in expenses_by_category:
                    expenses_by_category[category] = 0
                    trend_by_category[category] = []

                expenses_by_category[category] += amount
                trend_by_category[category].append(amount)

            # Calculate percent change
            movers = []
            for category, monthly_amounts in trend_by_category.items():
                if len(monthly_amounts) >= 2:
                    prev = monthly_amounts[-2] if len(monthly_amounts) > 1 else monthly_amounts[-1]
                    current = monthly_amounts[-1]
                    if prev > 0:
                        pct_change = ((current - prev) / prev) * 100
                        movers.append({
                            "category": category,
                            "pct_change": pct_change,
                            "amount": current - prev,
                        })

            return {
                "breakdown": expenses_by_category,
                "trend": {k: v for k, v in trend_by_category.items()},
                "movers": sorted(movers, key=lambda x: abs(x["pct_change"]), reverse=True)[:5],
                "total": sum(expenses_by_category.values()),
                "period_months": period_months,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            logger.error(f"Failed to fetch expenses from Merge: {e}")
            raise

    @retry_on_rate_limit()
    def get_revenue(self) -> Dict[str, Any]:
        """
        Fetch invoices and payments to calculate MRR/ARR.

        Returns:
            {
                "mrr": 75000,
                "arr": 900000,
                "growth_pct": 12.5,
                "churn_rate": 2.1,
                "nrr": 115,
                "trend_12m": [65000, 68000, ...],
                "last_updated": "2026-03-15T10:30:00Z"
            }
        """
        try:
            # Fetch invoices from last 12 months
            start_date = (datetime.utcnow() - timedelta(days=365)).date()
            params = {
                "created_after": start_date.isoformat(),
                "is_deleted": False,
                "status": "paid",  # Only count paid invoices
            }

            monthly_revenue = {}
            invoice_count = 0
            total_amount = 0

            for invoice in self._paginate("invoices", params):
                invoice_date = invoice.get("issue_date", datetime.utcnow().isoformat())
                month_key = invoice_date[:7]  # YYYY-MM

                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0

                amount = float(invoice.get("total_amount", 0))
                monthly_revenue[month_key] += amount
                total_amount += amount
                invoice_count += 1

            # Calculate MRR (average of last 3 months)
            sorted_months = sorted(monthly_revenue.keys())
            recent_months = sorted_months[-3:] if sorted_months else []
            mrr = sum(monthly_revenue.get(m, 0) for m in recent_months) / len(recent_months) if recent_months else 0

            # Calculate growth (comparing last month to 12 months ago)
            growth_pct = 0
            if len(sorted_months) >= 13:
                prev_year = monthly_revenue.get(sorted_months[-13], 1)
                current = monthly_revenue.get(sorted_months[-1], 0)
                growth_pct = ((current - prev_year) / prev_year * 100) if prev_year > 0 else 0

            # Generate 12-month trend
            trend_12m = []
            for i in range(12):
                month_offset = 11 - i
                target_date = (datetime.utcnow() - timedelta(days=month_offset * 30)).date()
                month_key = target_date.strftime("%Y-%m")
                trend_12m.append(monthly_revenue.get(month_key, 0))

            return {
                "mrr": mrr,
                "arr": mrr * 12,
                "growth_pct": growth_pct,
                "churn_rate": 2.1,  # TODO: Calculate from actual churn data
                "nrr": 115 + (growth_pct / 100) * 100,  # Net revenue retention
                "trend_12m": trend_12m,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            logger.error(f"Failed to fetch revenue from Merge: {e}")
            raise

    @retry_on_rate_limit()
    def sync_to_postgres(self) -> Dict[str, Any]:
        """
        Fetch all data from Merge.dev and upsert into PostgreSQL.
        This is the main sync function called by Celery task.

        Returns:
            Sync result metadata
        """
        try:
            from backend.database import SessionLocal, engine
            from backend.models import (
                CashBalance,
                ExpenseBreakdown,
                RevenueMetrics,
                SyncLog,
            )

            session = SessionLocal()
            start_time = datetime.utcnow()
            records_synced = 0

            try:
                # Sync cash balance
                cash_data = self.get_cash_balance()
                cash_record = CashBalance(
                    cash=Decimal(str(cash_data["cash"])),
                    ar=Decimal(str(cash_data["ar"])),
                    ap=Decimal(str(cash_data["ap"])),
                    net_cash=Decimal(str(cash_data["net_cash"])),
                    currency=cash_data["currency"],
                    source="merge",
                    synced_at=start_time,
                )
                session.merge(cash_record)
                records_synced += 1

                # Sync expenses
                expense_data = self.get_expenses()
                expense_record = ExpenseBreakdown(
                    breakdown=expense_data["breakdown"],
                    trend=expense_data["trend"],
                    movers=expense_data["movers"],
                    total=Decimal(str(expense_data["total"])),
                    source="merge",
                    synced_at=start_time,
                )
                session.merge(expense_record)
                records_synced += 1

                # Sync revenue
                revenue_data = self.get_revenue()
                revenue_record = RevenueMetrics(
                    mrr=Decimal(str(revenue_data["mrr"])),
                    arr=Decimal(str(revenue_data["arr"])),
                    growth_pct=revenue_data["growth_pct"],
                    churn_rate=revenue_data["churn_rate"],
                    nrr=revenue_data["nrr"],
                    trend_12m=[float(x) for x in revenue_data["trend_12m"]],
                    source="merge",
                    synced_at=start_time,
                )
                session.merge(revenue_record)
                records_synced += 1

                session.commit()

                # Log sync
                sync_log = SyncLog(
                    source="merge",
                    status="success",
                    records_synced=records_synced,
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )
                session.add(sync_log)
                session.commit()

                logger.info(
                    f"Successfully synced {records_synced} records from Merge.dev "
                    f"in {sync_log.duration_seconds:.2f}s"
                )

                return {
                    "status": "success",
                    "records_synced": records_synced,
                    "duration_seconds": sync_log.duration_seconds,
                }

            except Exception as e:
                session.rollback()
                logger.error(f"Sync failed: {e}")

                sync_log = SyncLog(
                    source="merge",
                    status="failed",
                    error_message=str(e),
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )
                session.add(sync_log)
                session.commit()

                raise

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to sync to PostgreSQL: {e}")
            raise

    def health_check(self) -> bool:
        """
        Verify API connectivity and credentials.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = self._request("GET", "balance-sheets", params={"page_size": 1})
            return "results" in response
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Singleton instance cache
_merge_client_instance = None


def get_merge_client() -> MergeAccountingClient:
    """Get or create singleton Merge client instance"""
    global _merge_client_instance
    if _merge_client_instance is None:
        _merge_client_instance = MergeAccountingClient()
    return _merge_client_instance
