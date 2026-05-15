from datetime import datetime

from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.commercial_engine import resolve_rules, status_from_approval_role


def repeat_order(db: Session, source_order: Order, seller_id: int | None = None) -> Order:
    """Cria uma recompra em orçamento a partir de um pedido existente."""
    new_order = Order(
        customer_id=source_order.customer_id,
        seller_id=seller_id or source_order.seller_id,
        carrier_id=source_order.carrier_id,
        payment_condition=source_order.payment_condition,
        delivery_location=source_order.delivery_location,
        freight_value=float(source_order.freight_value or 0),
        status="em_orcamento",
        created_at=datetime.utcnow(),
    )
    db.add(new_order)
    db.flush()

    gross = 0.0
    discount_total = 0.0
    rule_items: list[dict] = []

    for item in source_order.items:
        product = db.get(Product, item.product_id)
        unit_price = float(product.price_table if product and product.price_table is not None else item.unit_price or 0)
        qty = int(item.quantity or 1)
        discount = float(item.discount or 0)
        line_gross = unit_price * qty
        line_discount = line_gross * (discount / 100.0)
        line_total = line_gross - line_discount

        gross += line_gross
        discount_total += line_discount
        rule_items.append({"product_id": item.product_id, "quantity": qty, "discount": discount})

        db.add(
            OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=qty,
                unit_price=unit_price,
                discount=discount,
                total=line_total,
            )
        )

    new_order.total_gross = gross
    new_order.total_discount = discount_total
    new_order.total_net = gross - discount_total + float(new_order.freight_value or 0)

    rule_result = resolve_rules(
        db,
        customer_id=new_order.customer_id,
        seller_id=new_order.seller_id,
        items=rule_items,
    )
    new_order.status = "em_orcamento"
    new_order.commission_percent = rule_result.commission_percent
    new_order.commission_total = float(new_order.total_net or 0) * (float(rule_result.commission_percent or 0) / 100.0)
    new_order.approval_required_role = rule_result.approval_role
    new_order.max_discount_applied = rule_result.max_discount_used
    new_order.rule_summary = rule_result.rule_summary

    db.commit()
    db.refresh(new_order)
    return new_order
