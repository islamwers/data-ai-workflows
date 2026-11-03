"""A small, inspectable ETL example. All input rows are fictional."""
import csv
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {"organic", "paid search", "referral"}

def transform(rows):
    accepted, rejected, replaced = {}, [], []
    for line, row in enumerate(rows, 2):
        reason = None
        key = row["order_id"].strip()
        try:
            if not key:
                raise ValueError("missing order_id")
            day = date.fromisoformat(row["date"].strip()).isoformat()
            amount = Decimal(row["amount"].strip())
            if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal(".01")):
                raise ValueError("amount must be a non-negative finite value with at most two decimals")
            channel = row["channel"].strip().lower()
            if channel not in CHANNELS:
                raise ValueError("unsupported channel")
            if row["currency"].strip().upper() != "USD":
                raise ValueError("demo supports USD only")
        except (ValueError, InvalidOperation) as exc:
            reason = str(exc) if not isinstance(exc, InvalidOperation) else "invalid amount"
        if reason:
            rejected.append({"line": line, "order_id": key or None, "reason": reason})
            continue
        if key in accepted:
            replaced.append({"order_id": key, "policy": "last valid row in this file wins"})
        accepted[key] = {"order_id": key, "date": day, "channel": channel,
                         "amount": str(amount.quantize(Decimal(".01"))), "currency": "USD"}
    return list(accepted.values()), rejected, replaced

if __name__ == "__main__":
    with (ROOT / "etl/source.csv").open(newline="") as f:
        source = list(csv.DictReader(f))
    clean, rejects, replacements = transform(source)
    assert len(source) == 12 and len(clean) == 8 and len(rejects) == 3 and len(replacements) == 1
    assert next(r["amount"] for r in clean if r["order_id"] == "ORD-103") == "99.90"
    # Failure cases beyond the pictured fixture: never silently admit bad money or currencies.
    for update in ({"amount": "NaN"}, {"amount": "-1"}, {"amount": "1.001"}, {"currency": "EUR"}):
        rows, errors, _ = transform([{**source[0], **update}])
        assert not rows and len(errors) == 1
    output = {"mode": "synthetic fixture", "source_rows": len(source), "clean_rows": clean,
              "rejected": rejects, "replacements": replacements}
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/etl-transform.json").write_text(json.dumps(output, indent=2) + "\n")
    print("PASS: 12 source rows -> 8 clean orders; 3 rejected rows; 1 duplicate resolved.")
