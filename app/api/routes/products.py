from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.product import Product
from app.auth import current_user_from_cookie, is_admin
from app.services.company_context_service import company_context, require_active_company_or_redirect
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    code = data.get("code") or data.get("sku")
    if not code:
        code = data["name"][:40]
    obj = Product(
        company_id=data.get("company_id"),
        category_id=data.get("category_id"),
        code=code,
        name=data["name"],
        category=data.get("category"),
        unit=data.get("unit") or "UN",
        price_table=data.get("price") if data.get("price") is not None else data.get("price_table", 0),
        price_minimum=data.get("min_price") if data.get("min_price") is not None else data.get("price_minimum", 0),
        commission=data.get("commission_percent") if data.get("commission_percent") is not None else data.get("commission", 0),
        stock=data.get("stock", 0),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    obj.sku = obj.code
    obj.price = obj.price_table
    obj.min_price = obj.price_minimum
    obj.commission_percent = obj.commission
    return obj


web_router = APIRouter()


@web_router.get("/produtos")
def produtos_page(request: Request, db: Session = Depends(get_db)):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    products = db.query(Product).filter(Product.company_id == active_company.id).order_by(Product.id.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "produtos.html",
        {"request": request, "products": products, "current_user": current_user, "active_seller": current_user, "is_admin": is_admin(current_user), **company_context(request, db, current_user)},
    )


@web_router.post("/produtos")
def produtos_create(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    category: str = Form(""),
    unit: str = Form("UN"),
    price_table: float = Form(0),
    price_minimum: float = Form(0),
    commission: float = Form(0),
    stock: float = Form(0),
    db: Session = Depends(get_db),
):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    obj = Product(
        company_id=active_company.id,
        code=code,
        name=name,
        category=category or None,
        unit=unit,
        price_table=price_table,
        price_minimum=price_minimum,
        commission=commission,
        stock=stock,
    )
    db.add(obj)
    db.commit()
    return RedirectResponse(url="/produtos", status_code=303)
