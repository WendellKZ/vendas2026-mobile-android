from dataclasses import dataclass, field
from typing import Any


@dataclass
class ItemMarginResult:
    product_id: int | None
    product_name: str
    quantity: int
    unit_price: float
    cost_price: float
    discount_percent: float
    line_net: float
    margin_value: float
    margin_percent: float
    alerts: list[str] = field(default_factory=list)


@dataclass
class OrderIntelligenceResult:
    total_net: float
    total_cost: float
    margin_value: float
    margin_percent: float
    approval_required_role: str | None
    risk_level: str
    alerts: list[str]
    items: list[ItemMarginResult]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _get_product_cost(product: Any, unit_price: float) -> float:
    # Suporta campo futuro cost_price. Enquanto não existir no banco/modelo,
    # usa custo estimado de 65% do preço de venda para simulação comercial.
    cost = _safe_float(getattr(product, "cost_price", None), 0.0)
    if cost <= 0:
        cost = unit_price * 0.65
    return cost


def analyze_order_items(items: list[Any], approval_role: str | None = None) -> OrderIntelligenceResult:
    analyzed_items: list[ItemMarginResult] = []
    alerts: list[str] = []
    total_net = 0.0
    total_cost = 0.0
    max_discount = 0.0

    for item in items:
        product = getattr(item, "product", None)
        quantity = _safe_int(getattr(item, "quantity", 0), 0)
        unit_price = _safe_float(getattr(item, "unit_price", 0), 0.0)
        discount = _safe_float(getattr(item, "discount", 0), 0.0)
        line_net = _safe_float(getattr(item, "total", 0), 0.0)
        if line_net <= 0 and quantity > 0:
            gross = unit_price * quantity
            line_net = gross - (gross * discount / 100.0)

        cost_price = _get_product_cost(product, unit_price)
        line_cost = cost_price * quantity
        margin_value = line_net - line_cost
        margin_percent = (margin_value / line_net * 100.0) if line_net > 0 else 0.0
        item_alerts: list[str] = []

        if discount >= 10:
            item_alerts.append("Desconto alto no item")
        elif discount >= 5:
            item_alerts.append("Desconto moderado no item")

        if margin_percent < 10:
            item_alerts.append("Margem crítica")
        elif margin_percent < 20:
            item_alerts.append("Margem em atenção")

        max_discount = max(max_discount, discount)
        total_net += line_net
        total_cost += line_cost

        analyzed_items.append(
            ItemMarginResult(
                product_id=getattr(item, "product_id", None),
                product_name=getattr(product, "name", "Produto") if product else "Produto",
                quantity=quantity,
                unit_price=unit_price,
                cost_price=cost_price,
                discount_percent=discount,
                line_net=line_net,
                margin_value=margin_value,
                margin_percent=round(margin_percent, 2),
                alerts=item_alerts,
            )
        )

    margin_value = total_net - total_cost
    margin_percent = (margin_value / total_net * 100.0) if total_net > 0 else 0.0
    risk_level = "saudavel"
    required_role = approval_role

    if max_discount >= 10:
        alerts.append("Desconto alto: pedido deve passar por aprovação comercial.")
        required_role = required_role or "manager"
        risk_level = "atencao"
    elif max_discount >= 5:
        alerts.append("Desconto moderado: revise margem antes de finalizar.")
        risk_level = "atencao"

    if margin_percent < 10:
        alerts.append("Margem crítica: recomenda-se aprovação do administrador.")
        required_role = "admin"
        risk_level = "critico"
    elif margin_percent < 20:
        alerts.append("Margem baixa: recomenda-se aprovação do gestor.")
        required_role = required_role or "manager"
        if risk_level != "critico":
            risk_level = "atencao"

    if not alerts:
        alerts.append("Pedido com margem saudável e sem alerta comercial relevante.")

    return OrderIntelligenceResult(
        total_net=round(total_net, 2),
        total_cost=round(total_cost, 2),
        margin_value=round(margin_value, 2),
        margin_percent=round(margin_percent, 2),
        approval_required_role=required_role,
        risk_level=risk_level,
        alerts=alerts,
        items=analyzed_items,
    )
