from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.price_suggestion_service import suggest_price_for_product


@dataclass
class HistoricalPricingInsight:
    product_id: int | None
    product_name: str
    reference_sources: list[str]
    last_sale_price: float | None
    average_sale_price: float | None
    average_discount_percent: float | None
    sales_count: int
    suggested_price: float
    minimum_safe_price: float
    risk_level: str
    explanation: str
    confidence: str
    warnings: list[str] = field(default_factory=list)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _item_unit_net_price(item: OrderItem) -> float:
    quantity = max(int(item.quantity or 1), 1)
    total = _safe_float(item.total, 0.0)
    if total > 0:
        return total / quantity
    unit = _safe_float(item.unit_price, 0.0)
    discount = _safe_float(item.discount, 0.0)
    return unit - (unit * discount / 100.0)


def build_price_insight(
    db: Session,
    product_id: int,
    customer_id: int | None = None,
    seller_id: int | None = None,
    discount_percent: float = 0.0,
    limit: int = 30,
) -> HistoricalPricingInsight:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("Produto não encontrado")

    base_suggestion = suggest_price_for_product(product, discount_percent=discount_percent)

    query = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .options(joinedload(OrderItem.order), joinedload(OrderItem.product))
        .filter(OrderItem.product_id == product_id)
        .order_by(Order.id.desc())
    )

    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if seller_id:
        query = query.filter(Order.seller_id == seller_id)

    items = query.limit(limit).all()

    reference_sources = [
        "Preço atual cadastrado no produto",
        "Custo estimado em 65% do preço quando não houver custo real",
        "Margem mínima segura de 20%",
        "Margem alvo de 30%",
    ]

    warnings: list[str] = []
    confidence = "baixa"
    last_sale_price = None
    average_sale_price = None
    average_discount = None
    suggested_price = base_suggestion.ideal_price
    explanation = base_suggestion.recommendation

    if items:
        unit_prices = [_item_unit_net_price(item) for item in items if _item_unit_net_price(item) > 0]
        discounts = [_safe_float(item.discount, 0.0) for item in items]
        if unit_prices:
            last_sale_price = round(unit_prices[0], 2)
            average_sale_price = round(mean(unit_prices), 2)
            average_discount = round(mean(discounts), 2) if discounts else 0.0
            reference_sources.append("Histórico real de pedidos do produto")
            if customer_id:
                reference_sources.append("Histórico real do cliente selecionado")
            if seller_id:
                reference_sources.append("Histórico real do vendedor selecionado")

            # Combina preço ideal técnico com histórico de vendas para não sugerir algo fora da realidade comercial.
            suggested_price = round(max(base_suggestion.minimum_safe_price, (base_suggestion.ideal_price * 0.65) + (average_sale_price * 0.35)), 2)
            confidence = "alta" if len(unit_prices) >= 5 else "média"
            explanation = (
                "Sugestão calculada combinando margem segura, preço atual e histórico real de vendas. "
                "Quanto maior o histórico deste cliente/vendedor, mais confiável a sugestão."
            )
    else:
        warnings.append("Sem histórico suficiente para este filtro; sugestão baseada em margem e preço cadastrado.")

    if suggested_price < base_suggestion.minimum_safe_price:
        warnings.append("Preço sugerido abaixo do mínimo seguro; revise margem antes de vender.")

    return HistoricalPricingInsight(
        product_id=product.id,
        product_name=product.name,
        reference_sources=reference_sources,
        last_sale_price=last_sale_price,
        average_sale_price=average_sale_price,
        average_discount_percent=average_discount,
        sales_count=len(items),
        suggested_price=round(suggested_price, 2),
        minimum_safe_price=base_suggestion.minimum_safe_price,
        risk_level=base_suggestion.risk_level,
        explanation=explanation,
        confidence=confidence,
        warnings=warnings,
    )
