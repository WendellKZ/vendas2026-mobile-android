from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import current_user_from_cookie, is_admin
from app.db.deps import get_db
from app.models.commercial_rule import CommercialRule
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User

web_router = APIRouter()


def _ctx(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    sellers = db.query(User).filter(User.active == True).order_by(User.name).all()  # noqa
    return {"current_user": user, "active_seller": user, "sellers_menu": sellers, "is_admin": is_admin(user)}


def _admin_or_redirect(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    if not user:
        return None, RedirectResponse(url="/login", status_code=303)
    if not is_admin(user):
        return user, RedirectResponse(url="/painel", status_code=303)
    return user, None


@web_router.get("/regras")
def regras_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = _admin_or_redirect(request, db)
    if redirect:
        return redirect
    rules = db.query(CommercialRule).order_by(CommercialRule.active.desc(), CommercialRule.rule_type, CommercialRule.priority.desc()).all()
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).order_by(Product.name).all()
    sellers = db.query(User).order_by(User.name).all()
    return request.app.state.templates.TemplateResponse(
        "regras.html",
        {"request": request, "rules": rules, "customers": customers, "products": products, "sellers": sellers, **_ctx(request, db)},
    )


@web_router.post("/regras/novo")
def regra_create(
    request: Request,
    name: str = Form(...),
    rule_type: str = Form("discount"),
    scope: str = Form("global"),
    reference_id: str = Form(""),
    priority: int = Form(10),
    max_discount_percent: float = Form(5),
    approval_limit_manager: float = Form(5),
    approval_limit_admin: float = Form(10),
    commission_percent: float = Form(5),
    commission_high_discount_percent: float = Form(2),
    db: Session = Depends(get_db),
):
    user, redirect = _admin_or_redirect(request, db)
    if redirect:
        return redirect
    ref = int(reference_id) if reference_id and scope != "global" else None
    rule = CommercialRule(
        name=name.strip(), rule_type=rule_type, scope=scope, reference_id=ref, priority=priority,
        max_discount_percent=max_discount_percent, approval_limit_manager=approval_limit_manager,
        approval_limit_admin=approval_limit_admin, commission_percent=commission_percent,
        commission_high_discount_percent=commission_high_discount_percent, active=True,
    )
    db.add(rule)
    db.commit()
    return RedirectResponse(url="/regras", status_code=303)


@web_router.post("/regras/{rule_id}/status")
def regra_status(rule_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = _admin_or_redirect(request, db)
    if redirect:
        return redirect
    rule = db.get(CommercialRule, rule_id)
    if rule:
        rule.active = not bool(rule.active)
        db.commit()
    return RedirectResponse(url="/regras", status_code=303)


@web_router.post("/regras/{rule_id}/excluir")
def regra_delete(rule_id: int, request: Request, db: Session = Depends(get_db)):
    user, redirect = _admin_or_redirect(request, db)
    if redirect:
        return redirect
    rule = db.get(CommercialRule, rule_id)
    if rule:
        db.delete(rule)
        db.commit()
    return RedirectResponse(url="/regras", status_code=303)
