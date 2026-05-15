from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate
from app.services.commercial_engine import calculate_order_totals, resolve_rules, status_from_approval_role

APPROVAL_DISCOUNT_LIMIT = 10.0


def evaluate_order_status(discounts) -> str:
    max_discount = max([float(d or 0) for d in discounts], default=0.0)
    if max_discount > 10:
        return "em_aprovacao_admin"
    if max_discount > 5:
        return "em_aprovacao_gestor"
    return "aprovado"


def create_order(db: Session, payload: OrderCreate) -> Order:
    raw_items = [
        {
            "product_id": i.product_id,
            "quantity": i.quantity,
            "discount": i.discount_percent if i.discount_percent is not None else (i.discount or 0),
        }
        for i in payload.items
    ]
    rules = resolve_rules(db, customer_id=payload.customer_id, seller_id=payload.seller_id, items=raw_items)
    gross, total_discount, net_without_freight, normalized = calculate_order_totals(db, raw_items)
    total_net = net_without_freight + float(payload.freight_value or 0)
    commission_total = total_net * (float(rules.commission_percent or 0) / 100.0)

    order = Order(
        company_id=payload.company_id,
        customer_id=payload.customer_id,
        seller_id=payload.seller_id,
        carrier_id=payload.carrier_id,
        payment_condition=payload.payment_condition,
        delivery_location=payload.delivery_location,
        freight_value=payload.freight_value,
        status=status_from_approval_role(rules.approval_role),
        total_gross=gross,
        total_discount=total_discount,
        total_net=total_net,
    )
    if hasattr(order, "commission_percent"):
        order.commission_percent = rules.commission_percent
        order.commission_total = commission_total
        order.approval_required_role = rules.approval_role
        order.max_discount_applied = rules.max_discount_used
        order.rule_summary = rules.rule_summary

    db.add(order)
    db.flush()

    for item in normalized:
        db.add(OrderItem(order_id=order.id, product_id=item["product"].id, quantity=item["quantity"], unit_price=item["unit_price"], discount=item["discount"], total=item["total"]))

    db.commit()
    db.refresh(order)
    return order


def approve_order(db: Session, order_id: int) -> Order | None:
    order = db.get(Order, order_id)
    if not order:
        return None
    order.status = "aprovado"
    db.commit()
    db.refresh(order)
    return order
