from dataclasses import dataclass
from typing import Any


@dataclass
class PriceSuggestion:
    product_id: int | None
    product_name: str
    current_price: float
    estimated_cost: float
    ideal_price: float
    minimum_safe_price: float
    current_margin_percent: float
    ideal_margin_percent: float
    risk_level: str
    recommendation: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _estimated_cost(product: Any, current_price: float) -> float:
    cost = _safe_float(getattr(product, "cost_price", None), 0.0)
    if cost <= 0:
        cost = current_price * 0.65
    return cost


def suggest_price_for_product(product: Any, discount_percent: float = 0.0, target_margin_percent: float = 30.0) -> PriceSuggestion:
    current_price = _safe_float(getattr(product, "price_table", None), 0.0)
    if current_price <= 0:
        current_price = _safe_float(getattr(product, "price", None), 0.0)

    discount = max(0.0, _safe_float(discount_percent, 0.0))
    cost = _estimated_cost(product, current_price)
    current_net = current_price - (current_price * discount / 100.0)
    current_margin = ((current_net - cost) / current_net * 100.0) if current_net > 0 else 0.0

    target_margin = max(10.0, min(60.0, _safe_float(target_margin_percent, 30.0)))
    minimum_margin = 20.0

    ideal_price = cost / (1 - (target_margin / 100.0)) if target_margin < 100 else current_price
    minimum_safe_price = cost / (1 - (minimum_margin / 100.0))

    # Evita sugestão artificialmente menor que o preço atual em cenário saudável.
    if current_margin >= target_margin:
        ideal_price = max(current_price, ideal_price)

    ideal_margin = ((ideal_price - cost) / ideal_price * 100.0) if ideal_price > 0 else 0.0

    risk_level = "saudavel"
    recommendation = "Preço atual está saudável para a margem estimada."

    if current_margin < 10:
        risk_level = "critico"
        recommendation = "Preço atual deixa margem crítica. Recomenda-se elevar o preço ou reduzir desconto."
    elif current_margin < 20:
        risk_level = "atencao"
        recommendation = "Preço atual está com margem baixa. Use o preço mínimo seguro como referência."
    elif discount >= 10:
        risk_level = "atencao"
        recommendation = "Desconto alto detectado. Verifique se o preço final mantém margem suficiente."

    return PriceSuggestion(
        product_id=getattr(product, "id", None),
        product_name=getattr(product, "name", "Produto"),
        current_price=round(current_price, 2),
        estimated_cost=round(cost, 2),
        ideal_price=round(ideal_price, 2),
        minimum_safe_price=round(minimum_safe_price, 2),
        current_margin_percent=round(current_margin, 2),
        ideal_margin_percent=round(ideal_margin, 2),
        risk_level=risk_level,
        recommendation=recommendation,
    )
