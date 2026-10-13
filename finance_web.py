"""Local demo finance application used by the Playwright workflow."""
from decimal import Decimal, InvalidOperation
from flask import Flask, request, redirect, url_for, render_template_string
from storage import Storage

app = Flask(__name__)
storage = Storage()

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>OpenOps Finance</title>
<style>body{font-family:Arial,sans-serif;max-width:920px;margin:40px auto;padding:0 18px;color:#172033}h1{margin-bottom:4px}.muted{color:#64748b}form{display:grid;grid-template-columns:1fr 1fr;gap:14px;background:#f8fafc;padding:20px;border-radius:12px;margin:22px 0}label{display:flex;flex-direction:column;gap:6px;font-weight:600}input{padding:10px;border:1px solid #cbd5e1;border-radius:6px;font-size:15px}button{grid-column:1/-1;padding:12px;background:#1d4ed8;color:white;border:0;border-radius:6px;font-weight:700;cursor:pointer}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #e2e8f0}th{background:#f1f5f9}.notice{padding:12px;background:#dcfce7;border-radius:8px;margin:12px 0}.error{padding:12px;background:#fee2e2;border-radius:8px;margin:12px 0}</style></head>
<body><h1>OpenOps Finance</h1><p class="muted">Local demo app — records are stored in the project's SQLite database.</p>
{% if message %}<div class="notice" role="status" data-testid="success-message">{{ message }}</div>{% endif %}
{% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
<h2>Enter invoice</h2>
<form method="post" action="/invoices" data-testid="invoice-form">
<label>Invoice ID<input name="invoice_id" id="invoice_id" required value="{{ values.get('invoice_id','') }}"></label>
<label>Vendor<input name="vendor" id="vendor" required value="{{ values.get('vendor','') }}"></label>
<label>Amount<input name="amount" id="amount" type="number" min="0.01" step="0.01" required value="{{ values.get('amount','') }}"></label>
<label>Due date<input name="due_date" id="due_date" type="date" required value="{{ values.get('due_date','') }}"></label>
<input type="hidden" name="source_path" value="{{ values.get('source_path','browser-demo') }}">
<button type="submit" id="save-invoice">Save invoice</button></form>
<h2>Saved finance records</h2><table data-testid="records-table"><thead><tr><th>Record</th><th>Invoice ID</th><th>Vendor</th><th>Amount</th><th>Due date</th></tr></thead><tbody>
{% for r in records %}<tr data-invoice-id="{{ r['invoice_id'] }}"><td>{{ r['record_id'] }}</td><td>{{ r['invoice_id'] }}</td><td>{{ r['vendor'] }}</td><td>{{ r['amount'] }}</td><td>{{ r['due_date'] }}</td></tr>{% else %}<tr><td colspan="5">No records yet</td></tr>{% endfor %}
</tbody></table></body></html>'''


def get_records():
    with storage.connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT record_id, invoice_id, vendor, amount, due_date FROM finance_records ORDER BY record_id DESC"
        ).fetchall()]

@app.get("/")
def home():
    return render_template_string(PAGE, records=get_records(), message=request.args.get("message"), error=None, values={})

@app.post("/invoices")
def save_invoice():
    values = {k: request.form.get(k, "").strip() for k in ("invoice_id", "vendor", "amount", "due_date", "source_path")}
    try:
        amount = Decimal(values["amount"]).quantize(Decimal("0.01"))
        if amount <= 0 or not values["invoice_id"] or not values["vendor"]:
            raise ValueError("Invoice ID, vendor, and a positive amount are required.")
        if len(values["due_date"]) != 10:
            raise ValueError("A valid due date is required.")
    except (InvalidOperation, ValueError) as exc:
        return render_template_string(PAGE, records=get_records(), message=None, error=str(exc), values=values), 400
    with storage.connect() as conn:
        conn.execute("INSERT INTO finance_records(invoice_id,vendor,amount,due_date,source_path) VALUES(?,?,?,?,?) "
                      "ON CONFLICT(invoice_id) DO NOTHING",
                      (values["invoice_id"], values["vendor"], str(amount), values["due_date"], values["source_path"] or "browser-demo"))
        row = conn.execute("SELECT record_id,vendor,amount,due_date FROM finance_records WHERE invoice_id=?", (values["invoice_id"],)).fetchone()
    if row["vendor"].casefold() != values["vendor"].casefold() or Decimal(row["amount"]) != amount or row["due_date"] != values["due_date"]:
        return render_template_string(PAGE, records=get_records(), message=None, error="An invoice with this ID already exists with different details.", values=values), 409
    return redirect(url_for("home", message=f"Saved and verified invoice {values['invoice_id']} (record #{row['record_id']})."), code=303)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
