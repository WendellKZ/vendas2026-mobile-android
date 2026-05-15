from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.commercial_rule import CommercialRule
from app.models.product import Product

@dataclass
class RuleResult:
    max_discount_percent: float = 5.0
    approval_role: str = "auto"
    commission_percent: float = 5.0
    commission_total: float = 0.0
    max_discount_used: float = 0.0
    rule_summary: str = "Regra padrão"

def _rules(db: Session, rule_type: str):
    return db.query(CommercialRule).filter(CommercialRule.rule_type == rule_type, CommercialRule.active == True).order_by(CommercialRule.priority.desc(), CommercialRule.id.desc()).all()  # noqa

def _matches(rule, customer_id, seller_id, product_ids):
    return rule.scope == "global" or (rule.scope == "customer" and rule.reference_id == customer_id) or (rule.scope == "seller" and rule.reference_id == seller_id) or (rule.scope == "product" and rule.reference_id in product_ids)

def resolve_rules(db: Session, *, customer_id, seller_id, items):
    product_ids = {int(i.get("product_id")) for i in items if i.get("product_id")}
    max_used = max([float(i.get("discount") or 0) for i in items], default=0.0)
    res = RuleResult(max_discount_used=max_used)
    dr = next((r for r in _rules(db, "discount") if _matches(r, customer_id, seller_id, product_ids)), None)
    cr = next((r for r in _rules(db, "commission") if _matches(r, customer_id, seller_id, product_ids)), None)
    manager_limit, admin_limit = 5.0, 10.0
    if dr:
        res.max_discount_percent = float(dr.max_discount_percent or 0)
        manager_limit = float(dr.approval_limit_manager or 5)
        admin_limit = float(dr.approval_limit_admin or 10)
        res.rule_summary = f"Desconto: {dr.name}"
    res.approval_role = "auto" if max_used <= manager_limit else ("manager" if max_used <= admin_limit else "admin")
    if cr:
        res.commission_percent = float(cr.commission_high_discount_percent if max_used > res.max_discount_percent and cr.commission_high_discount_percent else cr.commission_percent or 0)
        res.rule_summary += f" | Comissão: {cr.name}"
    return res

def calculate_order_totals(db: Session, items):
    gross = total_discount = 0.0
    normalized = []
    for item in items:
        product = db.get(Product, int(item.get("product_id"))) if item.get("product_id") else None
        if not product: continue
        qty, disc, unit = int(item.get("quantity") or 1), float(item.get("discount") or 0), float(product.price_table or 0)
        line_gross = unit * qty
        line_discount = line_gross * disc / 100.0
        total = line_gross - line_discount
        gross += line_gross; total_discount += line_discount
        normalized.append({"product": product, "quantity": qty, "discount": disc, "unit_price": unit, "total": total})
    return gross, total_discount, gross - total_discount, normalized

def status_from_approval_role(role: str):
    return "em_aprovacao_gestor" if role == "manager" else ("em_aprovacao_admin" if role == "admin" else "aprovado")
