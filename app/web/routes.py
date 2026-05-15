from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.branch import Branch
from app.models.category import Category
from app.models.company import Company
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment_condition import PaymentCondition
from app.models.price_table import PriceTable, PriceTableItem
from app.models.product import Product
from app.models.stock import Stock
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import approve_order, create_order

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def money(value: object) -> str:
    try:
        value = Decimal(str(value or 0))
    except Exception:
        value = Decimal('0')
    text = f"{value:,.2f}"
    return text.replace(',', 'X').replace('.', ',').replace('X', '.')


def status_label(status: str) -> str:
    labels = {
        'aprovado': 'Aprovado',
        'em_aprovacao': 'Em aprovação',
        'rascunho': 'Rascunho',
        'cancelado': 'Cancelado',
    }
    return labels.get(status, status.replace('_', ' ').title())


templates.env.filters['money'] = money
templates.env.filters['status_label'] = status_label


def get_dashboard_data(db: Session) -> dict:
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_sellers = db.query(func.count(User.id)).filter(User.role == 'vendedor').scalar() or 0
    net_sales = db.query(func.coalesce(func.sum(Order.net_total), 0)).filter(Order.status.in_(['aprovado', 'em_aprovacao'])).scalar() or 0
    pending_approval = db.query(func.count(Order.id)).filter(Order.status == 'em_aprovacao').scalar() or 0
    recent_orders = db.query(Order).options(joinedload(Order.customer), joinedload(Order.seller)).order_by(Order.created_at.desc()).limit(8).all()
    by_status = defaultdict(int)
    for status, qty in db.query(Order.status, func.count(Order.id)).group_by(Order.status).all():
        by_status[status] = qty

    low_stock = (
        db.query(Stock)
        .options(joinedload(Stock.product), joinedload(Stock.branch))
        .filter(Stock.quantity <= 10)
        .order_by(Stock.quantity.asc())
        .limit(5)
        .all()
    )

    return {
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'total_sellers': total_sellers,
        'net_sales': net_sales,
        'pending_approval': pending_approval,
        'recent_orders': recent_orders,
        'by_status': by_status,
        'low_stock': low_stock,
    }


@router.get('/painel')
def dashboard(request: Request, db: Session = Depends(get_db)):
    context = {'request': request, 'page': 'painel'}
    context.update(get_dashboard_data(db))
    return templates.TemplateResponse('dashboard.html', context)


@router.get('/clientes')
def customers_page(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).options(joinedload(Customer.company), joinedload(Customer.default_price_table)).order_by(Customer.id.desc()).all()
    companies = db.query(Company).order_by(Company.name).all()
    price_tables = db.query(PriceTable).order_by(PriceTable.name).all()
    return templates.TemplateResponse('customers.html', {
        'request': request, 'page': 'clientes', 'customers': customers, 'companies': companies, 'price_tables': price_tables
    })


@router.post('/clientes/novo')
def customers_create(
    company_id: int = Form(...),
    name: str = Form(...),
    document: str = Form(...),
    city: str = Form(''),
    status: str = Form('ativo'),
    segment: str = Form('geral'),
    default_price_table_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    customer = Customer(
        company_id=company_id,
        name=name,
        document=document,
        city=city,
        status=status,
        segment=segment,
        default_price_table_id=default_price_table_id,
    )
    db.add(customer)
    db.commit()
    return RedirectResponse('/clientes', status_code=303)


@router.get('/produtos')
def products_page(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).options(joinedload(Product.company), joinedload(Product.category)).order_by(Product.id.desc()).all()
    companies = db.query(Company).order_by(Company.name).all()
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse('products.html', {
        'request': request, 'page': 'produtos', 'products': products, 'companies': companies, 'categories': categories
    })


@router.post('/produtos/novo')
def products_create(
    company_id: int = Form(...),
    category_id: int | None = Form(None),
    sku: str = Form(...),
    name: str = Form(...),
    unit: str = Form('UN'),
    price: float = Form(...),
    min_price: float = Form(...),
    commission_percent: float = Form(0),
    db: Session = Depends(get_db),
):
    product = Product(
        company_id=company_id,
        category_id=category_id,
        sku=sku,
        name=name,
        unit=unit,
        price=price,
        min_price=min_price,
        commission_percent=commission_percent,
    )
    db.add(product)
    db.commit()
    return RedirectResponse('/produtos', status_code=303)


@router.get('/pedidos')
def orders_page(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).options(joinedload(Order.customer), joinedload(Order.seller), joinedload(Order.branch)).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse('orders.html', {
        'request': request, 'page': 'pedidos', 'orders': orders
    })


@router.post('/pedidos/{order_id}/aprovar')
def orders_approve(order_id: int, db: Session = Depends(get_db)):
    approve_order(db, order_id)
    return RedirectResponse('/pedidos', status_code=303)


@router.get('/pedidos/novo')
def order_form(request: Request, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    branches = db.query(Branch).order_by(Branch.name).all()
    customers = db.query(Customer).order_by(Customer.name).all()
    sellers = db.query(User).order_by(User.name).all()
    products = db.query(Product).order_by(Product.name).all()
    payment_conditions = db.query(PaymentCondition).order_by(PaymentCondition.name).all()
    return templates.TemplateResponse('order_form.html', {
        'request': request, 'page': 'pedidos', 'companies': companies, 'branches': branches, 'customers': customers,
        'sellers': sellers, 'products': products, 'payment_conditions': payment_conditions
    })


@router.post('/pedidos/novo')
def order_create(
    company_id: int = Form(...),
    branch_id: int = Form(...),
    customer_id: int = Form(...),
    seller_id: int = Form(...),
    payment_condition_id: int | None = Form(None),
    freight_value: float = Form(0),
    product_id: list[int] = Form(...),
    quantity: list[float] = Form(...),
    discount_percent: list[float] = Form(...),
    db: Session = Depends(get_db),
):
    items = []
    for p_id, qty, discount in zip(product_id, quantity, discount_percent):
        if qty and qty > 0:
            items.append(OrderItemCreate(product_id=p_id, quantity=qty, discount_percent=discount))

    payload = OrderCreate(
        company_id=company_id,
        branch_id=branch_id,
        customer_id=customer_id,
        seller_id=seller_id,
        payment_condition_id=payment_condition_id,
        freight_value=freight_value,
        items=items,
    )
    create_order(db, payload)
    return RedirectResponse('/pedidos', status_code=303)


@router.get('/configuracoes')
def settings_page(request: Request, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    branches = db.query(Branch).options(joinedload(Branch.company)).order_by(Branch.id.desc()).all()
    sellers = db.query(User).order_by(User.id.desc()).all()
    categories = db.query(Category).order_by(Category.name).all()
    price_tables = db.query(PriceTable).options(joinedload(PriceTable.company)).order_by(PriceTable.id.desc()).all()
    payments = db.query(PaymentCondition).order_by(PaymentCondition.id.desc()).all()
    return templates.TemplateResponse('settings.html', {
        'request': request, 'page': 'configuracoes', 'companies': companies, 'branches': branches, 'sellers': sellers,
        'categories': categories, 'price_tables': price_tables, 'payments': payments
    })


@router.post('/configuracoes/empresa')
def create_company(name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Company(name=name))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)


@router.post('/configuracoes/filial')
def create_branch(company_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Branch(company_id=company_id, name=name))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)


@router.post('/configuracoes/vendedor')
def create_seller(company_id: int = Form(...), name: str = Form(...), email: str = Form(...), role: str = Form('vendedor'), max_discount_percent: float = Form(0), db: Session = Depends(get_db)):
    db.add(User(company_id=company_id, name=name, email=email, role=role, max_discount_percent=max_discount_percent))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)


@router.post('/configuracoes/categoria')
def create_category(name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Category(name=name))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)


@router.post('/configuracoes/tabela-preco')
def create_price_table(company_id: int = Form(...), name: str = Form(...), is_default: str = Form('false'), db: Session = Depends(get_db)):
    db.add(PriceTable(company_id=company_id, name=name, is_default=str(is_default).lower() == 'true'))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)


@router.post('/configuracoes/condicao-pagamento')
def create_payment(name: str = Form(...), installments: int = Form(1), interest_percent: float = Form(0), entry_percent: float = Form(0), db: Session = Depends(get_db)):
    db.add(PaymentCondition(name=name, installments=installments, interest_percent=interest_percent, entry_percent=entry_percent))
    db.commit()
    return RedirectResponse('/configuracoes', status_code=303)
