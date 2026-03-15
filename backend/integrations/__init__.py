"""
Integrations module for external accounting systems.

Provides unified interfaces for:
- Merge.dev (production QuickBooks, Xero, etc.)
- ERPNext (development simulator)
"""

from .merge_client import MergeAccountingClient, get_merge_client

__all__ = [
    "MergeAccountingClient",
    "get_merge_client",
]
