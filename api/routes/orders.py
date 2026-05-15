from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
import json

from app.db.deps import get_db
from app.models.carrier import Carrier
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import create_order

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
web_router = APIRouter()


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value else None


def _upsert_order_items(
    db: Session,
    order: Order,
    product_ids: list[int],
    quantities: list[int],
    discounts: list[float],
) -> None:
    db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()

    gross = 0.0
    total_discount_value = 0.0

    for idx, pid in enumerate(product_ids):
        if not pid:
            continue
        quantity = int(quantities[idx]) if idx < len(quantities) else 1
        discount_percent = float(discounts[idx]) if idx < len(discounts) else 0.0
        product = db.get(Product, pid)
        if not product:
            continue

        line_gross = float(product.price_table) * quantity
        line_discount_value = line_gross * (discount_percent / 100.0)
        line_total = line_gross - line_discount_value

        gross += line_gross
        total_discount_value += line_discount_value

        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=float(product.price_table),
                discount=discount_percent,
                total=line_total,
            )
        )

    order.total_gross = gross
    order.total_discount = total_discount_value
    order.total_net = gross - total_discount_value + float(order.freight_value or 0)


@router.get("/", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).options(joinedload(Order.items)).order_by(Order.id.desc()).all()


@router.post("/", response_model=OrderRead, status_code=201)
def create_order_api(payload: OrderCreate, db: Session = Depends(get_db)):
    return create_order(db, payload)


@web_router.get("/pedidos")
def pedidos_page(request: Request, db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.carrier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .order_by(Order.id.desc())
        .all()
    )
    return request.app.state.templates.TemplateResponse("pedidos.html", {"request": request, "orders": orders})


@web_router.get("/pedidos/novo")
def pedidos_novo_page(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).order_by(Product.name).all()
    sellers = db.query(User).order_by(User.name).all()
    carriers = db.query(Carrier).order_by(Carrier.name).all()
    return request.app.state.templates.TemplateResponse(
        "pedido_novo.html",
        {
            "request": request,
            "customers": customers,
            "products": products,
            "sellers": sellers,
            "carriers": carriers,
            "page_title": "Novo pedido",
            "page_subtitle": "Monte o pedido com vários itens, resumo financeiro e conferência antes de integrar",
            "form_action": "/pedidos/novo",
            "selected_customer_id": None,
            "selected_seller_id": None,
            "selected_payment_condition": "28 dias",
            "selected_carrier_id": None,
            "selected_delivery_location": "",
            "initial_items_json": "[]",
            "is_edit": False,
        },
    )


@web_router.post("/pedidos/novo")
def pedidos_novo_create(
    request: Request,
    customer_id: int = Form(...),
    seller_id: str = Form(""),
    carrier_id: str = Form(""),
    payment_condition: str = Form("28 dias"),
    delivery_location: str = Form(""),
    product_id: list[int] | None = Form(None),
    quantity: list[int] | None = Form(None),
    discount: list[float] | None = Form(None),
    db: Session = Depends(get_db),
):
    product_ids = product_id or []
    quantities = quantity or []
    discounts = discount or []

    items = []
    for idx, pid in enumerate(product_ids):
        qty = int(quantities[idx]) if idx < len(quantities) else 1
        disc = float(discounts[idx]) if idx < len(discounts) else 0.0
        if pid:
            items.append({"product_id": int(pid), "quantity": qty, "discount": disc})

    if not items:
        return RedirectResponse(url="/pedidos/novo", status_code=303)

    payload = OrderCreate(
        customer_id=customer_id,
        seller_id=_parse_optional_int(seller_id),
        carrier_id=_parse_optional_int(carrier_id),
        payment_condition=payment_condition,
        delivery_location=delivery_location or None,
        freight_value=0,
        items=items,
    )
    create_order(db, payload)
    return RedirectResponse(url="/pedidos", status_code=303)


@web_router.get("/pedidos/editar/{order_id}")
def pedido_editar_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.carrier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.status != "em_orcamento":
        raise HTTPException(status_code=400, detail="Apenas pedidos em orçamento podem ser editados")

    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).order_by(Product.name).all()
    sellers = db.query(User).order_by(User.name).all()
    carriers = db.query(Carrier).order_by(Carrier.name).all()

    initial_items = [
        {
            "product_id": item.product_id,
            "code": item.product.code if item.product else "",
            "name": item.product.name if item.product else "Item",
            "quantity": item.quantity,
            "discount": item.discount,
            "price": float(item.unit_price or 0),
            "stock": float(item.product.stock) if item.product else 0,
        }
        for item in order.items
    ]

    return request.app.state.templates.TemplateResponse(
        "pedido_editar.html",
        {
            "request": request,
            "order": order,
            "customers": customers,
            "products": products,
            "sellers": sellers,
            "carriers": carriers,
            "page_title": f"Editar pedido #{order.id}",
            "page_subtitle": "Você pode alterar pedidos enquanto estiverem em orçamento.",
            "form_action": f"/pedidos/editar/{order.id}",
            "selected_customer_id": order.customer_id,
            "selected_seller_id": order.seller_id,
            "selected_payment_condition": order.payment_condition or "28 dias",
            "selected_carrier_id": order.carrier_id,
            "selected_delivery_location": order.delivery_location or "",
            "initial_items_json": json.dumps(initial_items),
            "is_edit": True,
        },
    )


@web_router.post("/pedidos/editar/{order_id}")
def pedido_editar_save(
    order_id: int,
    customer_id: int = Form(...),
    seller_id: str = Form(""),
    carrier_id: str = Form(""),
    payment_condition: str = Form("28 dias"),
    delivery_location: str = Form(""),
    product_id: list[int] | None = Form(None),
    quantity: list[int] | None = Form(None),
    discount: list[float] | None = Form(None),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.status != "em_orcamento":
        raise HTTPException(status_code=400, detail="Apenas pedidos em orçamento podem ser editados")

    product_ids = product_id or []
    quantities = quantity or []
    discounts = discount or []

    if not product_ids:
        return RedirectResponse(url=f"/pedidos/editar/{order_id}", status_code=303)

    order.customer_id = customer_id
    order.seller_id = _parse_optional_int(seller_id)
    order.carrier_id = _parse_optional_int(carrier_id)
    order.payment_condition = payment_condition
    order.delivery_location = delivery_location or None
    order.freight_value = 0

    _upsert_order_items(db, order, product_ids, quantities, discounts)
    db.commit()
    return RedirectResponse(url="/pedidos", status_code=303)


@web_router.get("/pedidos/conferir/{order_id}")
def pedido_conferir(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.carrier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    return request.app.state.templates.TemplateResponse(
        "pedido_conferir.html",
        {"request": request, "order": order},
    )


@web_router.post("/pedidos/integrar/{order_id}")
def pedido_integrar(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.status != "em_orcamento":
        return RedirectResponse(url="/pedidos", status_code=303)

    order.status = "enviado_erp"
    db.commit()
    return RedirectResponse(url="/pedidos", status_code=303)
