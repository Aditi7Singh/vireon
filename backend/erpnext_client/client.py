import httpx
import os
import json
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ERPNextClient:
    """
    Client for interacting with ERPNext REST API with production-ready features:
    - Persistent HTTPX session
    - Retry logic
    - Circuit breaker (basic implementation)
    - Caching for resource lists
    - Bidirectional sync support (GET/POST/PUT/DELETE)
    """
    def __init__(self, base_url: str, api_key: str, api_secret: str, site_name: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if site_name:
            self.headers["Host"] = site_name
        self._client: Optional[httpx.AsyncClient] = None
        
        # Circuit breaker state
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._circuit_open = False
        self._failure_threshold = 5
        self._reset_timeout = 60 # seconds
        
        # Simple Cache
        self._cache = {} # (doctype, filters_str) -> (timestamp, data)
        self._cache_ttl = 300 # 5 minutes

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _check_circuit(self):
        if self._circuit_open:
            if self._last_failure_time and (datetime.now() - self._last_failure_time).total_seconds() > self._reset_timeout:
                logger.info("Circuit breaker: Attempting to reset (Half-Open)")
                self._circuit_open = False
                self._failure_count = 0
            else:
                raise Exception("Circuit breaker is OPEN. ERPNext API is currently unavailable.")

    def _report_success(self):
        self._failure_count = 0
        self._circuit_open = False

    def _report_failure(self):
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        if self._failure_count >= self._failure_threshold:
            logger.error(f"Circuit breaker: Opening circuit after {self._failure_count} failures")
            self._circuit_open = True

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        self._check_circuit()
        
        url = f"{self.base_url}{path}"
        client = await self.get_client()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                self._report_success()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Retry on rate limit or server errors
                if e.response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Error {e.response.status_code} on attempt {attempt+1}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                self._report_failure()
                error_details = e.response.text
                logger.error(f"HTTP error occurred: {e.response.status_code} - {error_details}")
                # Also print to console for the user to see easily
                print(f"❌ HTTP Error {e.response.status_code}: {error_details}")
                raise
            except (httpx.RequestError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error on attempt {attempt+1}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                self._report_failure()
                raise

    async def get_resource_list(self, doctype: str, filters: Optional[Dict] = None, fields: Optional[List[str]] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Generic GET for any DocType list. Includes basic caching.
        """
        filters_str = str(filters) if filters else ""
        cache_key = (doctype, filters_str)
        
        if use_cache and cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if (datetime.now() - ts).total_seconds() < self._cache_ttl:
                return data

        path = f"/api/resource/{doctype}"
        params = {}
        if filters:
            params["filters"] = json.dumps(filters)
        if fields:
            params["fields"] = json.dumps(fields)
        
        result = await self._request("GET", path, params=params)
        data = result.get("data", [])
        
        if use_cache:
            self._cache[cache_key] = (datetime.now(), data)
        
        return data

    async def get_doc(self, doctype: str, name: str) -> Dict[str, Any]:
        path = f"/api/resource/{doctype}/{name}"
        result = await self._request("GET", path)
        return result.get("data", {})

    async def create_doc(self, doctype: str, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/api/resource/{doctype}"
        result = await self._request("POST", path, json=data)
        return result.get("data", {})

    async def update_doc(self, doctype: str, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/api/resource/{doctype}/{name}"
        result = await self._request("PUT", path, json=data)
        return result.get("data", {})

    async def delete_doc(self, doctype: str, name: str):
        path = f"/api/resource/{doctype}/{name}"
        await self._request("DELETE", path)

    # --- Domain Specific Methods ---

    async def get_sales_invoices(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list(
            "Sales Invoice", 
            fields=["name", "customer", "posting_date", "grand_total", "status", "outstanding_amount"]
        )

    async def get_purchase_invoices(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list(
            "Purchase Invoice", 
            fields=["name", "supplier", "posting_date", "grand_total", "status", "outstanding_amount"]
        )

    async def get_gl_entries(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        filters = [
            ["posting_date", ">=", from_date],
            ["posting_date", "<=", to_date]
        ]
        return await self.get_resource_list("GL Entry", filters=filters)

    async def get_payment_entries(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list(
            "Payment Entry", 
            fields=["name", "posting_date", "paid_amount", "received_amount", "payment_type", "party"]
        )

    async def sync_resource(self, doctype: str, data: Dict[str, Any], match_fields: List[str]) -> Dict[str, Any]:
        """
        Bidirectional sync: Upsert based on match_fields.
        """
        filters = {field: data[field] for field in match_fields if field in data}
        existing = await self.get_resource_list(doctype, filters=filters, fields=["name"], use_cache=False)
        
        if existing:
            doc_name = existing[0]["name"]
            return await self.update_doc(doctype, doc_name, data)
        else:
            return await self.create_doc(doctype, data)

    # --- Missing Enterprise Features ---

    async def get_bank_transactions(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list("Bank Transaction")

    async def get_budgets(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list("Budget")

    async def get_assets(self) -> List[Dict[str, Any]]:
        return await self.get_resource_list("Asset")
