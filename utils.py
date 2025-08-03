\
from typing import Dict, Any, List
import math

def compute_markdown_price(list_price: float, stage: int) -> float:
    schedule = {0:0.00, 1:0.10, 2:0.25, 3:0.40}
    pct = schedule.get(stage, 0.0)
    return round(list_price * (1.0 - pct), 2)

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def compute_payouts(rows: List[dict]) -> List[dict]:
    """
    rows: [{"consignor_id","name","pix_key","percent","total_net"}]
    Returns list with consignor_value and shop_value.
    """
    out = []
    for r in rows:
        total = safe_float(r.get("total_net", 0.0))
        pct   = safe_float(r.get("percent", 0.5))
        consignor_value = round(total * pct, 2)
        shop_value      = round(total - consignor_value, 2)
        out.append({**r, "consignor_value": consignor_value, "shop_value": shop_value})
    return out
