from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class TaskIntent:
    workflow: str
    vendor: str
    original_request: str

@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    vendor: str
    amount: Decimal
    due_date: str
    invoice_date: str
    source_path: str

@dataclass(frozen=True)
class FinanceRecord:
    record_id: int
    invoice_id: str
    vendor: str
    amount: Decimal
    due_date: str
    source_path: str

@dataclass(frozen=True)
class AgentResult:
    success: bool
    message: str
    invoice: Optional[Invoice] = None
    record: Optional[FinanceRecord] = None
    task_id: Optional[str] = None
