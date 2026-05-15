from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.auth import verify_password
from app.db.deps import get_db
from app.models.carrier import Carrier
from app.models.commercial_rule import CommercialRule
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.payment_condition import PaymentCondition
from app.models.product import Product
from app.models.user import User
from app.services.commercial_engine import calculate_order_totals, resolve_rules, status_from_approval_role

router = APIRouter(prefix="/mobile", tags=["mobile-sync"])

class MobileLoginPayload(BaseModel):
    email: str
    password: str

class MobileOrderItemPayload(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    discount: float = Field(default=0, ge=0)

class MobileOrderPayload(BaseModel):
    mobile_uuid: str
    customer_id: int
    seller_id: int | None = None
    carrier_id: int | None = None
    payment_condition: str | None = None
    delivery_location: str | None = None
    freight_value: float = 0
    items: list[MobileOrderItemPayload]

def _make_token(user: User) -> str:
    base = f"{user.id}:{user.email}:{user.password_hash or ''}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"v8.{user.id}.{digest}"

def _current_mobile_user(db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token mobile ausente")
    token = authorization.split(" ", 1)[1].strip()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v8":
        raise HTTPException(status_code=401, detail="Token mobile inválido")
    try:
        user_id = int(parts[1])
    except ValueError:
        raise HTTPException(status_code=401, detail="Token mobile inválido")
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Usuário mobile inativo ou não encontrado")
    if token != _make_token(user):
        raise HTTPException(status_code=401, detail="Token mobile expirado")
    return user

def _obj(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {field: getattr(obj, field, None) for field in fields}

@router.post("/login")
def mobile_login(payload: MobileLoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    return {
        "token": _make_token(user),
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "company_id": user.company_id, "branch_id": user.branch_id},
    }

@router.get("/sync/bootstrap")
def mobile_bootstrap(since: str | None = None, db: Session = Depends(get_db), user: User = Depends(_current_mobile_user)):
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).order_by(Product.name).all()
    carriers = db.query(Carrier).order_by(Carrier.name).all()
    rules = db.query(CommercialRule).filter(CommercialRule.active == True).order_by(CommercialRule.priority.desc()).all()  # noqa: E712
    try:
        payment_conditions = db.query(PaymentCondition).order_by(PaymentCondition.name).all()
    except Exception:
        payment_conditions = []
    return {
        "server_time": datetime.utcnow().isoformat(),
        "seller": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        "customers": [_obj(c, ["id", "name", "corporate_name", "document", "state_registration", "city", "delivery_location", "email", "phone", "billing_email", "status", "suframa"]) for c in customers],
        "products": [{"id": p.id, "code": getattr(p, "code", None), "name": p.name, "category": p.category, "unit": p.unit, "price_table": float(p.price_table or 0), "price_minimum": float(p.price_minimum or 0), "commission": float(p.commission or 0), "stock": float(p.stock or 0)} for p in products],
        "carriers": [_obj(c, ["id", "name", "document", "city", "phone", "email"]) for c in carriers],
        "payment_conditions": [{"id": pc.id, "name": pc.name, "installments": pc.installments, "interest_percent": float(pc.interest_percent or 0), "entry_percent": float(pc.entry_percent or 0)} for pc in payment_conditions] or [{"id": 1, "name": "À vista", "installments": 1, "interest_percent": 0, "entry_percent": 100}, {"id": 2, "name": "28 dias", "installments": 1, "interest_percent": 0, "entry_percent": 0}, {"id": 3, "name": "28/35/42 dias", "installments": 3, "interest_percent": 0, "entry_percent": 0}],
        "commercial_rules": [{"id": r.id, "name": r.name, "rule_type": r.rule_type, "scope": r.scope, "reference_id": r.reference_id, "priority": r.priority, "max_discount_percent": float(r.max_discount_percent or 0), "approval_limit_manager": float(r.approval_limit_manager or 0), "approval_limit_admin": float(r.approval_limit_admin or 0), "commission_percent": float(r.commission_percent or 0), "commission_high_discount_percent": float(r.commission_high_discount_percent or 0)} for r in rules],
    }

@router.post("/pedidos/sync")
def mobile_sync_order(payload: MobileOrderPayload, db: Session = Depends(get_db), user: User = Depends(_current_mobile_user)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Pedido sem itens")
    existing = db.query(Order).filter(Order.mobile_uuid == payload.mobile_uuid).first()
    if existing:
        return {"status": "already_synced", "order_id": existing.id, "mobile_uuid": existing.mobile_uuid, "order_status": existing.status, "message": "Pedido já tinha sido sincronizado anteriormente"}
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="Cliente não encontrado na base web")
    seller_id = payload.seller_id if user.role == "admin" and payload.seller_id else user.id
    items_dict = [item.model_dump() for item in payload.items]
    gross, total_discount, net, normalized = calculate_order_totals(db, items_dict)
    if not normalized:
        raise HTTPException(status_code=400, detail="Nenhum produto válido no pedido")
    rule_result = resolve_rules(db, customer_id=payload.customer_id, seller_id=seller_id, items=items_dict)
    order_status = status_from_approval_role(rule_result.approval_role)
    final_net = net + float(payload.freight_value or 0)
    order = Order(customer_id=payload.customer_id, seller_id=seller_id, carrier_id=payload.carrier_id, status=order_status, payment_condition=payload.payment_condition or "", delivery_location=payload.delivery_location or customer.delivery_location or "", freight_value=float(payload.freight_value or 0), total_gross=gross, total_discount=total_discount, total_net=final_net, commission_percent=rule_result.commission_percent, commission_total=final_net * (rule_result.commission_percent / 100.0), approval_required_role=None if rule_result.approval_role == "auto" else rule_result.approval_role, max_discount_applied=rule_result.max_discount_used, rule_summary=rule_result.rule_summary, mobile_uuid=payload.mobile_uuid, mobile_status="sincronizado", sync_source="android_offline", synced_at=datetime.utcnow())
    db.add(order)
    db.flush()
    for row in normalized:
        db.add(OrderItem(order_id=order.id, product_id=row["product"].id, quantity=row["quantity"], unit_price=row["unit_price"], discount=row["discount"], total=row["total"]))
    db.commit()
    db.refresh(order)
    return {"status": "synced", "order_id": order.id, "mobile_uuid": order.mobile_uuid, "order_status": order.status, "approval_required_role": order.approval_required_role, "total_net": float(order.total_net or 0), "commission_total": float(order.commission_total or 0), "message": "Pedido recebido pela Web com sucesso"}

@router.get("/pedidos/status")
def mobile_orders_status(db: Session = Depends(get_db), user: User = Depends(_current_mobile_user)):
    query = db.query(Order).options(joinedload(Order.customer)).filter(Order.sync_source == "android_offline")
    if user.role != "admin":
        query = query.filter(Order.seller_id == user.id)
    orders = query.order_by(Order.id.desc()).limit(100).all()
    return {"orders": [{"id": o.id, "mobile_uuid": o.mobile_uuid, "customer": o.customer.name if o.customer else "", "status": o.status, "mobile_status": o.mobile_status, "total_net": float(o.total_net or 0), "synced_at": o.synced_at.isoformat() if o.synced_at else None} for o in orders]}
