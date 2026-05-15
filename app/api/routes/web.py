from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.auth import current_user_from_cookie, hash_password, is_admin, verify_password
from app.db.deps import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.services.company_context_service import ACTIVE_COMPANY_COOKIE, company_context, get_active_company

router = APIRouter()


def get_user_context(request: Request, db: Session):
    current_user = current_user_from_cookie(request, db)
    sellers = db.query(User).filter(User.active == True).order_by(User.name).all()  # noqa: E712
    ctx = {"sellers_menu": sellers, "active_seller": current_user, "current_user": current_user, "is_admin": is_admin(current_user)}
    ctx.update(company_context(request, db, current_user))
    return ctx


def require_user(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    if not user:
        return None
    return user


def apply_seller_filter(query, current_user):
    if current_user and current_user.role != "admin":
        return query.filter(Order.seller_id == current_user.id)
    return query


@router.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    if not current_user_from_cookie(request, db):
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url="/painel", status_code=303)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if current_user_from_cookie(request, db):
        return RedirectResponse(url="/painel", status_code=303)
    return request.app.state.templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not user.active or not verify_password(password, user.password_hash):
        return request.app.state.templates.TemplateResponse("login.html", {"request": request, "error": "E-mail ou senha inválidos."})
    target = "/painel"
    from app.services.company_context_service import get_allowed_companies
    allowed_companies = get_allowed_companies(db, user)
    if len(allowed_companies) != 1:
        target = "/selecionar-empresa"
    response = RedirectResponse(url=target, status_code=303)
    response.set_cookie("user_id", str(user.id), max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
    if len(allowed_companies) == 1:
        response.set_cookie(ACTIVE_COMPANY_COOKIE, str(allowed_companies[0].id), max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
    else:
        response.delete_cookie(ACTIVE_COMPANY_COOKIE)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie(ACTIVE_COMPANY_COOKIE)
    return response


@router.post("/sessao/vendedor")
def escolher_vendedor(seller_id: str = Form("")):
    # Compatibilidade visual antiga: login real agora controla o vendedor ativo.
    return RedirectResponse(url="/painel", status_code=303)


@router.get("/painel")
def painel(request: Request, db: Session = Depends(get_db)):
    current_user = require_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    ctx = get_user_context(request, db)
    active_company = ctx.get("active_company")
    active_company_id = active_company.id if active_company else None

    orders_query = apply_seller_filter(db.query(Order), current_user)
    if active_company_id and hasattr(Order, "company_id"):
        orders_query = orders_query.filter(Order.company_id == active_company_id)

    # V16: clientes são compartilhados entre empresas; catálogo/produtos são separados por empresa.
    customers_query = db.query(Customer)
    products_query = db.query(Product)
    if active_company_id:
        products_query = products_query.filter(Product.company_id == active_company_id)

    total_customers = customers_query.with_entities(func.count(Customer.id)).scalar() or 0
    total_products = products_query.with_entities(func.count(Product.id)).scalar() or 0
    total_orders = orders_query.with_entities(func.count(Order.id)).scalar() or 0
    total_sales = orders_query.with_entities(func.coalesce(func.sum(Order.total_net), 0)).scalar() or 0
    avg_ticket = (float(total_sales or 0) / total_orders) if total_orders else 0
    inventory_value = products_query.with_entities(func.coalesce(func.sum(Product.price_table * Product.stock), 0)).scalar() or 0
    low_stock_count = products_query.filter(Product.stock > 0, Product.stock <= 5).count()
    out_stock_count = products_query.filter(Product.stock <= 0).count()
    low_stock_products = products_query.filter(Product.stock <= 5).order_by(Product.stock.asc(), Product.name.asc()).limit(6).all()
    base_orders_for_counts = apply_seller_filter(db.query(Order), current_user)
    if active_company_id and hasattr(Order, "company_id"):
        base_orders_for_counts = base_orders_for_counts.filter(Order.company_id == active_company_id)
    approval_count = base_orders_for_counts.filter(Order.status.in_(["em_aprovacao", "em_aprovacao_gestor", "em_aprovacao_admin"])).count()
    open_count = base_orders_for_counts.filter(Order.status == "em_orcamento").count()

    recent_orders = (
        base_orders_for_counts
        .options(joinedload(Order.customer), joinedload(Order.seller), joinedload(Order.items).joinedload(OrderItem.product))
        .order_by(Order.id.desc())
        .limit(6)
        .all()
    )

    top_products = (
        base_orders_for_counts
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .with_entities(Product.name, func.coalesce(func.sum(OrderItem.total), 0).label("total"), func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"))
        .group_by(Product.id, Product.name)
        .order_by(func.coalesce(func.sum(OrderItem.total), 0).desc())
        .limit(5)
        .all()
    )

    top_customers = (
        base_orders_for_counts
        .join(Customer, Customer.id == Order.customer_id)
        .with_entities(Customer.name, func.coalesce(func.sum(Order.total_net), 0).label("total"), func.count(Order.id).label("orders"))
        .group_by(Customer.id, Customer.name)
        .order_by(func.coalesce(func.sum(Order.total_net), 0).desc())
        .limit(5)
        .all()
    )


    top_sellers_query = db.query(Order)
    if active_company_id and hasattr(Order, "company_id"):
        top_sellers_query = top_sellers_query.filter(Order.company_id == active_company_id)
    top_sellers = (
        top_sellers_query
        .join(User, User.id == Order.seller_id)
        .with_entities(
            User.name,
            func.coalesce(func.sum(Order.total_net), 0).label("total"),
            func.coalesce(func.sum(Order.commission_total), 0).label("commission"),
            func.count(Order.id).label("orders"),
        )
        .group_by(User.id, User.name)
        .order_by(func.coalesce(func.sum(Order.total_net), 0).desc())
        .limit(5)
        .all()
    )

    total_commission = base_orders_for_counts.with_entities(func.coalesce(func.sum(Order.commission_total), 0)).scalar() or 0

    return request.app.state.templates.TemplateResponse(
        "painel.html",
        {
            "request": request,
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "avg_ticket": avg_ticket,
            "inventory_value": inventory_value,
            "low_stock_count": low_stock_count,
            "out_stock_count": out_stock_count,
            "low_stock_products": low_stock_products,
            "approval_count": approval_count,
            "open_count": open_count,
            "recent_orders": recent_orders,
            "top_products": top_products,
            "top_customers": top_customers,
            "top_sellers": top_sellers,
            "total_commission": total_commission,
            **ctx,
        },
    )


@router.get("/configuracoes")
def configuracoes(request: Request, db: Session = Depends(get_db)):
    current_user = require_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return request.app.state.templates.TemplateResponse(
        "configuracoes.html",
        {"request": request, **get_user_context(request, db)},
    )
