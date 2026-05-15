from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from urllib.parse import quote
from datetime import datetime, timedelta
import json

from app.auth import current_user_from_cookie, is_admin
from app.db.deps import get_db
from app.models.carrier import Carrier
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import APPROVAL_DISCOUNT_LIMIT, create_order, evaluate_order_status
from app.services.commercial_engine import resolve_rules, status_from_approval_role
from app.services.company_context_service import company_context, require_active_company_or_redirect

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
web_router = APIRouter()




def format_order_datetime(value):
    if not value:
        return "Data não informada"
    try:
        return value.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return str(value)


def order_day_badge(value):
    if not value:
        return "Sem data"
    try:
        order_date = value.date()
        today = datetime.now().date()
        if order_date == today:
            return "Hoje"
        if order_date == today - timedelta(days=1):
            return "Ontem"
        return value.strftime("%d/%m")
    except Exception:
        return "Sem data"

def _parse_optional_int(value):
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value else None


def _money(v):
    return f"{float(v or 0):.2f}".replace(".", ",")


def build_whatsapp_message(order: Order) -> str:
    lines = []
    lines.append(f"📦 *PEDIDO #{order.id}*")
    lines.append("")
    lines.append(f"👤 Cliente: {order.customer.name if order.customer else '-'}")
    lines.append(f"🚚 Entrega: {order.delivery_location or '-'}")
    lines.append(f"🚛 Transportadora: {order.carrier.name if order.carrier else '-'}")
    lines.append("")
    lines.append("📋 *Itens do pedido:*")

    for item in order.items:
        nome = item.product.name if item.product else "Produto"
        unit = float(item.unit_price or 0)
        total = float(item.total or 0)

        lines.append(f"- {nome}")
        lines.append(f"  Qtd: {item.quantity} | Unit: R$ {_money(unit)} | Desc: {item.discount}%")
        lines.append(f"  Total: R$ {_money(total)}")
        lines.append("")

    lines.append("💰 *Resumo:*")
    lines.append(f"Bruto: R$ {_money(order.total_gross)}")
    lines.append(f"Desconto: R$ {_money(order.total_discount)}")
    lines.append(f"Total: R$ {_money(order.total_net)}")
    lines.append("")
    lines.append(f"💳 Pagamento: {order.payment_condition or '-'}")

    return quote("\n".join(lines))


def build_email_body(order: Order) -> str:
    lines = []
    lines.append(f"PEDIDO #{order.id}")
    lines.append("")
    lines.append(f"Cliente: {order.customer.name if order.customer else '-'}")
    lines.append(f"Entrega: {order.delivery_location or '-'}")
    lines.append(f"Transportadora: {order.carrier.name if order.carrier else '-'}")
    lines.append("")
    lines.append("Itens do pedido:")

    for item in order.items:
        nome = item.product.name if item.product else "Produto"
        unit = float(item.unit_price or 0)
        total = float(item.total or 0)

        lines.append(f"- {nome}")
        lines.append(f"  Qtd: {item.quantity} | Unit: R$ {_money(unit)} | Desc: {item.discount}%")
        lines.append(f"  Total: R$ {_money(total)}")
        lines.append("")

    lines.append("Resumo:")
    lines.append(f"Bruto: R$ {_money(order.total_gross)}")
    lines.append(f"Desconto: R$ {_money(order.total_discount)}")
    lines.append(f"Total: R$ {_money(order.total_net)}")
    lines.append("")
    lines.append(f"Pagamento: {order.payment_condition or '-'}")

    return quote("\n".join(lines))




def _validate_order_stock(db: Session, order: Order) -> list[str]:
    alerts: list[str] = []
    for item in order.items:
        product = item.product or db.get(Product, item.product_id)
        if not product:
            continue
        available = float(product.stock or 0)
        requested = float(item.quantity or 0)
        if requested > available:
            alerts.append(f"{product.code} - {product.name}: solicitado {requested:g}, disponível {available:g}")
    return alerts


def _deduct_order_stock(db: Session, order: Order) -> None:
    for item in order.items:
        product = item.product or db.get(Product, item.product_id)
        if not product:
            continue
        product.stock = max(0, float(product.stock or 0) - float(item.quantity or 0))


def _restore_order_stock(db: Session, order: Order) -> None:
    for item in order.items:
        product = item.product or db.get(Product, item.product_id)
        if not product:
            continue
        product.stock = float(product.stock or 0) + float(item.quantity or 0)

def _upsert_order_items(db, order, product_ids, quantities, discounts):
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
        # V16: itens do pedido só podem usar produtos do catálogo da empresa ativa.
        if getattr(order, "company_id", None) and getattr(product, "company_id", None) != order.company_id:
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


def _seller_context(request: Request, db: Session):
    sellers = db.query(User).filter(User.active == True).order_by(User.name).all()  # noqa: E712
    current_user = current_user_from_cookie(request, db)
    return sellers, current_user


def _require_logged(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    if not user:
        return None
    return user


def _filter_by_seller(query, current_user):
    if current_user and current_user.role != "admin":
        return query.filter(Order.seller_id == current_user.id)
    return query




def _route_context(request: Request, db: Session, user: User | None, sellers_menu=None):
    ctx = {
        "sellers_menu": sellers_menu if sellers_menu is not None else db.query(User).filter(User.active == True).order_by(User.name).all(),  # noqa: E712
        "active_seller": user,
        "current_user": user,
        "is_admin": is_admin(user),
    }
    ctx.update(company_context(request, db, user))
    return ctx

def _can_access_order(order: Order, current_user: User | None) -> bool:
    if not current_user:
        return False
    return current_user.role == "admin" or order.seller_id == current_user.id


@web_router.get("/pedidos")
def pedidos_page(request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    sellers_menu, active_seller = _seller_context(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    orders = (
        _filter_by_seller(db.query(Order), active_seller).filter(Order.company_id == active_company.id)
        .options(
            joinedload(Order.customer),
            joinedload(Order.seller),
            joinedload(Order.carrier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .order_by(Order.id.desc())
        .all()
    )
    return request.app.state.templates.TemplateResponse(
        "pedidos.html",
        {
            "request": request,
            "orders": orders,
            "build_whatsapp_message": build_whatsapp_message,
            "build_email_body": build_email_body,
            "format_order_datetime": format_order_datetime,
            "order_day_badge": order_day_badge,
            **_route_context(request, db, active_seller, sellers_menu),
        },
    )


@web_router.get("/pedidos/novo")
def pedidos_novo_page(request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    sellers_menu, active_seller = _seller_context(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).filter(Product.company_id == active_company.id).order_by(Product.name).all()
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
            "selected_seller_id": active_seller.id if active_seller else None,
            "selected_payment_condition": "28 dias",
            "selected_carrier_id": None,
            "selected_delivery_location": "",
            "initial_items_json": "[]",
            "is_edit": False,
            "discount_limit": APPROVAL_DISCOUNT_LIMIT,
            **_route_context(request, db, active_seller, sellers_menu),
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
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    if current_user.role != "admin":
        seller_id = str(current_user.id)
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

    # V16: garante que o vendedor só consiga incluir itens do catálogo da empresa ativa.
    valid_product_ids = {pid for (pid,) in db.query(Product.id).filter(Product.company_id == active_company.id).all()}
    items = [item for item in items if item["product_id"] in valid_product_ids]
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
    order = create_order(db, payload)
    order.company_id = active_company.id
    db.commit()
    return RedirectResponse(url=f"/pedidos/conferir/{order.id}", status_code=303)


@web_router.get("/pedidos/editar/{order_id}")
def pedido_editar_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.seller),
            joinedload(Order.carrier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_access_order(order, current_user):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
    if order.status not in ["em_orcamento", "aprovado"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos em orçamento ou aprovados podem ser reabertos/editados")

    sellers_menu, active_seller = _seller_context(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).filter(Product.company_id == active_company.id).order_by(Product.name).all()
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
            "page_subtitle": "Pedidos em orçamento e aprovados podem ser editados. Pedidos integrados ficam bloqueados.",
            "form_action": f"/pedidos/editar/{order.id}",
            "selected_customer_id": order.customer_id,
            "selected_seller_id": order.seller_id,
            "selected_payment_condition": order.payment_condition or "28 dias",
            "selected_carrier_id": order.carrier_id,
            "selected_delivery_location": order.delivery_location or "",
            "initial_items_json": json.dumps(initial_items),
            "is_edit": True,
            "discount_limit": APPROVAL_DISCOUNT_LIMIT,
            **_route_context(request, db, active_seller, sellers_menu),
        },
    )


@web_router.post("/pedidos/editar/{order_id}")
def pedido_editar_save(
    order_id: int,
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
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    order = db.get(Order, order_id)
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_access_order(order, current_user):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
    if current_user.role != "admin":
        seller_id = str(current_user.id)
    if order.status not in ["em_orcamento", "aprovado"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos em orçamento ou aprovados podem ser reabertos/editados")

    product_ids = product_id or []
    quantities = quantity or []
    discounts = discount or []
    if not product_ids:
        return RedirectResponse(url=f"/pedidos/editar/{order_id}", status_code=303)

    # V16: mantém o pedido preso ao catálogo da empresa ativa.
    valid_product_ids = {pid for (pid,) in db.query(Product.id).filter(Product.company_id == active_company.id).all()}
    filtered = [(pid, quantities[i] if i < len(quantities) else 1, discounts[i] if i < len(discounts) else 0) for i, pid in enumerate(product_ids) if pid in valid_product_ids]
    if not filtered:
        return RedirectResponse(url=f"/pedidos/editar/{order_id}", status_code=303)
    product_ids = [x[0] for x in filtered]
    quantities = [x[1] for x in filtered]
    discounts = [x[2] for x in filtered]

    order.company_id = active_company.id
    order.customer_id = customer_id
    order.seller_id = _parse_optional_int(seller_id)
    order.carrier_id = _parse_optional_int(carrier_id)
    order.payment_condition = payment_condition
    order.delivery_location = delivery_location or None
    _upsert_order_items(db, order, product_ids, quantities, discounts)
    rule_result = resolve_rules(
        db,
        customer_id=order.customer_id,
        seller_id=order.seller_id,
        items=[
            {
                "product_id": int(pid),
                "quantity": int(quantities[i]) if i < len(quantities) else 1,
                "discount": float(discounts[i]) if i < len(discounts) else 0,
            }
            for i, pid in enumerate(product_ids)
            if pid
        ],
    )
    order.status = status_from_approval_role(rule_result.approval_role)
    order.commission_percent = rule_result.commission_percent
    order.commission_total = float(order.total_net or 0) * (float(rule_result.commission_percent or 0) / 100.0)
    order.approval_required_role = rule_result.approval_role
    order.max_discount_applied = rule_result.max_discount_used
    order.rule_summary = rule_result.rule_summary
    db.commit()
    return RedirectResponse(url=f"/pedidos/conferir/{order_id}", status_code=303)


@web_router.post("/pedidos/integrar/{order_id}")
def pedido_integrar(order_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    order = db.get(Order, order_id)
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_access_order(order, current_user):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
    if order.status in ["em_aprovacao", "em_aprovacao_gestor", "em_aprovacao_admin"]:
        raise HTTPException(status_code=400, detail="Pedido precisa ser aprovado pela alçada antes da integração")
    stock_alerts = _validate_order_stock(db, order)
    if stock_alerts:
        raise HTTPException(status_code=400, detail="Estoque insuficiente: " + "; ".join(stock_alerts))
    if order.status != "integrado":
        _deduct_order_stock(db, order)
    order.status = "integrado"
    db.commit()
    return RedirectResponse(url="/pedidos", status_code=303)


@web_router.post("/pedidos/aprovar/{order_id}")
def pedido_aprovar(order_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    order = db.get(Order, order_id)
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.status == 'em_aprovacao_admin' and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode aprovar este pedido")
    if order.status == 'em_aprovacao_gestor' and current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Apenas gestor ou admin pode aprovar este pedido")
    order.status = "aprovado"
    db.commit()
    return RedirectResponse(url="/pedidos", status_code=303)


@web_router.post("/pedidos/cancelar/{order_id}")
def pedido_cancelar(order_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    order = db.get(Order, order_id)
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_access_order(order, current_user):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
    if order.status == "integrado":
        _restore_order_stock(db, order)
    order.status = "cancelado"
    db.commit()
    return RedirectResponse(url="/pedidos", status_code=303)

@web_router.get("/pedidos/conferir/{order_id}")
def pedido_conferir(order_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
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
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    if not order or order.company_id != active_company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not _can_access_order(order, current_user):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este pedido")
    sellers_menu, active_seller = _seller_context(request, db)
    return request.app.state.templates.TemplateResponse(
        "pedido_conferir.html",
        {"request": request, "order": order, "discount_limit": APPROVAL_DISCOUNT_LIMIT, **_route_context(request, db, active_seller, sellers_menu)},
    )