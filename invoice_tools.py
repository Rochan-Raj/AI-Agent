from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from models import Invoice

INVOICE_DIR = Path(__file__).parent / "data" / "invoices"

def field(text, name):
    match = re.search(rf"^{re.escape(name)}\s*:\s*(.*?)\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError(f"Missing required invoice field: {name}")
    return match.group(1).strip()

def parse_invoice(path):
    text = path.read_text(encoding="utf-8")
    invoice_id = field(text, "Invoice ID")
    vendor = field(text, "Vendor")
    raw = field(text, "Amount").replace(",", "").replace("$", "").replace("₹", "").strip()
    try:
        amount = Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount in {path.name}") from exc
    if amount <= 0:
        raise ValueError(f"Invoice amount must be positive in {path.name}")
    due_date = field(text, "Due Date")
    invoice_date = field(text, "Invoice Date")
    for label, value in (("Due Date", due_date), ("Invoice Date", invoice_date)):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError(f"{label} must use YYYY-MM-DD format in {path.name}")
    return Invoice(invoice_id, vendor, amount, due_date, invoice_date, str(path))

def find_latest_invoice(vendor, invoice_dir=INVOICE_DIR):
    matches = []
    if not invoice_dir.exists():
        raise FileNotFoundError(f"Invoice folder not found: {invoice_dir}")
    for path in invoice_dir.glob("*.txt"):
        try:
            invoice = parse_invoice(path)
        except ValueError:
            continue
        if invoice.vendor.casefold() == vendor.casefold():
            matches.append(invoice)
    if not matches:
        raise FileNotFoundError(f"No valid invoice found for vendor '{vendor}'.")
    return max(matches, key=lambda x: (x.invoice_date, x.invoice_id))
