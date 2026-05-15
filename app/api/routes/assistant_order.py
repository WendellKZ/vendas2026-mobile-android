from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import current_user_from_cookie, is_admin
from app.db.deps import get_db
from app.models.carrier import Carrier
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services.order_service import create_order

web_router = APIRouter()


def _require_logged(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    if not user:
        return None
    return user


def _parse_optional_int(value):
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value else None


def _user_context(request: Request, db: Session, current_user: User):
    sellers = db.query(User).filter(User.active == True).order_by(User.name).all()  # noqa: E712
    return {
        "sellers_menu": sellers,
        "active_seller": current_user,
        "current_user": current_user,
        "is_admin": is_admin(current_user),
    }


@web_router.get("/assistente-pedido")
def assistente_pedido(request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).order_by(Product.name).all()
    carriers = db.query(Carrier).order_by(Carrier.name).all()
    sellers = db.query(User).filter(User.active == True).order_by(User.name).all()  # noqa: E712

    top_products = (
        db.query(Product)
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .with_entities(
            Product.id,
            Product.code,
            Product.name,
            Product.category,
            Product.unit,
            Product.price_table,
            Product.stock,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("sold_qty"),
        )
        .group_by(Product.id, Product.code, Product.name, Product.category, Product.unit, Product.price_table, Product.stock)
        .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc(), Product.name.asc())
        .limit(8)
        .all()
    )

    seller_filter = [] if is_admin(current_user) else [Order.seller_id == current_user.id]

    favorite_customers = (
        db.query(Customer.id, Customer.name, func.count(Order.id).label("orders_count"))
        .join(Order, Order.customer_id == Customer.id)
        .filter(*seller_filter)
        .group_by(Customer.id, Customer.name)
        .order_by(func.count(Order.id).desc(), Customer.name.asc())
        .limit(6)
        .all()
    )

    favorite_products = (
        db.query(
            Product.id,
            Product.code,
            Product.name,
            Product.category,
            Product.unit,
            Product.price_table,
            Product.stock,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(*seller_filter)
        .group_by(Product.id, Product.code, Product.name, Product.category, Product.unit, Product.price_table, Product.stock)
        .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc(), Product.name.asc())
        .limit(8)
        .all()
    )

    preferred_payment_row = (
        db.query(Order.payment_condition, func.count(Order.id).label("uses"))
        .filter(Order.payment_condition.isnot(None), *seller_filter)
        .group_by(Order.payment_condition)
        .order_by(func.count(Order.id).desc())
        .first()
    )

    preferred_carrier_row = (
        db.query(Carrier.id, Carrier.name, func.count(Order.id).label("uses"))
        .join(Order, Order.carrier_id == Carrier.id)
        .filter(*seller_filter)
        .group_by(Carrier.id, Carrier.name)
        .order_by(func.count(Order.id).desc(), Carrier.name.asc())
        .first()
    )

    assistant_memory = {
        "seller_id": current_user.id,
        "seller_name": current_user.name,
        "preferred_payment": preferred_payment_row[0] if preferred_payment_row else "28 dias",
        "preferred_carrier_id": preferred_carrier_row[0] if preferred_carrier_row else "",
        "preferred_carrier_name": preferred_carrier_row[1] if preferred_carrier_row else "Definir depois",
        "favorite_customers": [{"id": c.id, "name": c.name, "orders_count": c.orders_count} for c in favorite_customers],
        "favorite_products": [{"id": p.id, "code": p.code, "name": p.name, "qty": int(p.qty or 0)} for p in favorite_products],
    }

    return request.app.state.templates.TemplateResponse(
        "assistente_pedido.html",
        {
            "request": request,
            "title": "Assistente de Pedido",
            "subtitle": "Fluxo guiado para representantes: cliente, pagamento, transporte, produtos e envio sem complicação.",
            "customers": customers,
            "products": products,
            "carriers": carriers,
            "sellers": sellers,
            "top_products": favorite_products if favorite_products else top_products,
            "assistant_memory": assistant_memory,
            "payment_options": ["À vista", "7 dias", "14 dias", "21 dias", "28 dias", "28/35 dias", "28/35/42 dias", "30/60 dias"],
            **_user_context(request, db, current_user),
        },
    )


@web_router.post("/assistente-pedido/finalizar")
def assistente_pedido_finalizar(
    request: Request,
    customer_id: int = Form(...),
    seller_id: str = Form(""),
    carrier_id: str = Form(""),
    payment_condition: str = Form("28 dias"),
    delivery_location: str = Form(""),
    assistant_action: str = Form("finalizar"),
    product_id: list[int] | None = Form(None),
    quantity: list[int] | None = Form(None),
    discount: list[float] | None = Form(None),
    db: Session = Depends(get_db),
):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    if current_user.role != "admin":
        seller_id = str(current_user.id)

    product_ids = product_id or []
    quantities = quantity or []
    discounts = discount or []
    items = []

    for idx, pid in enumerate(product_ids):
        if not pid:
            continue
        product = db.get(Product, int(pid))
        if not product:
            continue
        qty = int(quantities[idx]) if idx < len(quantities) else 1
        disc = float(discounts[idx]) if idx < len(discounts) else 0.0
        if qty <= 0:
            continue
        items.append({"product_id": int(pid), "quantity": qty, "discount": disc})

    if not items:
        return RedirectResponse(url="/assistente-pedido?erro=sem_itens", status_code=303)

    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    payload = OrderCreate(
        customer_id=customer_id,
        seller_id=_parse_optional_int(seller_id) or current_user.id,
        carrier_id=_parse_optional_int(carrier_id),
        payment_condition=payment_condition,
        delivery_location=delivery_location or customer.delivery_location or None,
        freight_value=0,
        items=items,
    )
    order = create_order(db, payload)

    # Opção pensada para representantes que ainda estão negociando com o cliente:
    # mantém o pedido como orçamento, mesmo que as regras comerciais permitam aprovação automática.
    if assistant_action == "orcamento":
        order.status = "em_orcamento"
        db.commit()
        db.refresh(order)
        return RedirectResponse(url="/pedidos", status_code=303)

    return RedirectResponse(url=f"/pedidos/conferir/{order.id}", status_code=303)
