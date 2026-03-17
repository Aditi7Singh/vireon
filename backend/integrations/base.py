from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date

class ERPAdapter(ABC):
    @abstractmethod
    async def get_invoices(self, from_date: date = None, to_date: date = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_contacts(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_accounts(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_balance_sheet(self) -> Dict[str, Any]:
        pass
