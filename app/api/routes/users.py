from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import current_user_from_cookie, hash_password, is_admin
from app.db.deps import get_db
from app.models.company import Company
from app.models.user import User
from app.models.user_company import UserCompany
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/api/v1/users", tags=["users"])
web_router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    obj = User(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _user_context(request: Request, db: Session):
    current_user = current_user_from_cookie(request, db)
    return {
        "current_user": current_user,
        "active_seller": current_user,
        "is_admin": is_admin(current_user),
    }


def _load_companies(db: Session):
    companies = db.query(Company).order_by(Company.name).all()
    if companies:
        return companies

    rows = db.execute(
        text("SELECT id, name, document FROM companies ORDER BY name")
    ).mappings().all()

    return [
        type(
            "CompanyLite",
            (),
            {"id": row["id"], "name": row["name"], "document": row["document"]},
        )()
        for row in rows
    ]


def _set_user_companies(db: Session, user_id: int, company_ids: list[int]) -> None:
    db.query(UserCompany).filter(UserCompany.user_id == user_id).delete()

    unique_ids: list[int] = []
    for company_id in company_ids or []:
        try:
            cid = int(company_id)
        except (TypeError, ValueError):
            continue
        if cid not in unique_ids:
            unique_ids.append(cid)

    for company_id in unique_ids:
        if db.get(Company, company_id):
            db.add(UserCompany(user_id=user_id, company_id=company_id))

    db.commit()


def _company_ids_from_form(company_ids) -> list[int]:
    if company_ids is None:
        return []
    if not isinstance(company_ids, list):
        company_ids = [company_ids]

    result: list[int] = []
    for value in company_ids:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _redirect_error(message: str) -> RedirectResponse:
    return RedirectResponse(url=f"/vendedores?erro={message}", status_code=303)


def _unique_login(db: Session, base_login: str) -> str:
    login = base_login
    suffix = 1
    while db.query(User).filter(User.email == login).first():
        prefix, _, domain = base_login.partition("@")
        if domain:
            login = f"{prefix}{suffix}@{domain}"
        else:
            login = f"{base_login}{suffix}"
        suffix += 1
    return login


def _normalize_email_or_generate(db: Session, email: str, name: str) -> str:
    email = (email or "").strip().lower()
    if email:
        return email
    base = "".join(ch for ch in (name or "vendedor").strip().lower().replace(" ", ".") if ch.isalnum() or ch == ".")
    if not base:
        base = "vendedor"
    return _unique_login(db, f"{base}@local")


@web_router.get("/vendedores")
def vendedores_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.name).all()
    companies = _load_companies(db)

    user_company_map = {}
    for link in db.query(UserCompany).all():
        user_company_map.setdefault(link.user_id, set()).add(link.company_id)

    return request.app.state.templates.TemplateResponse(
        "vendedores.html",
        {
            "request": request,
            "users": users,
            "companies": companies,
            "user_company_map": user_company_map,
            "erro": request.query_params.get("erro"),
            "title": "Vendedores",
            "subtitle": "Cadastre vendedores e defina quais empresas eles podem representar.",
            **_user_context(request, db),
        },
    )


@web_router.post("/vendedores")
def vendedores_create(
    request: Request,
    name: str = Form(...),
    email: str = Form(""),
    role: str = Form("seller"),
    password: str = Form("123456"),
    active: str = Form("1"),
    company_ids: list[int] | None = Form(None),
    db: Session = Depends(get_db),
):
    name = (name or "").strip()
    if not name:
        return _redirect_error("Nome%20obrigatorio")

    email = _normalize_email_or_generate(db, email, name)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return _redirect_error("Email%20ja%20cadastrado")

    user = User(
        name=name,
        email=email,
        role=role or "seller",
        password_hash=hash_password(password or "123456"),
        active=active == "1",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    _set_user_companies(db, user.id, _company_ids_from_form(company_ids))
    return RedirectResponse(url="/vendedores", status_code=303)


@web_router.get("/vendedores/editar/{user_id}")
def vendedor_edit_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/vendedores", status_code=303)

    companies = _load_companies(db)
    selected_company_ids = {
        link.company_id
        for link in db.query(UserCompany).filter(UserCompany.user_id == user_id).all()
    }

    return request.app.state.templates.TemplateResponse(
        "vendedor_editar.html",
        {
            "request": request,
            "user": user,
            "companies": companies,
            "selected_company_ids": selected_company_ids,
            "title": f"Editar vendedor #{user.id}",
            "subtitle": "Atualize dados do vendedor e empresas autorizadas.",
            **_user_context(request, db),
        },
    )


@web_router.post("/vendedores/editar/{user_id}")
def vendedor_edit_save(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(""),
    role: str = Form("seller"),
    password: str = Form(""),
    active: str = Form("1"),
    company_ids: list[int] | None = Form(None),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/vendedores", status_code=303)

    name = (name or "").strip()
    if not name:
        return RedirectResponse(url=f"/vendedores/editar/{user_id}?erro=Nome%20obrigatorio", status_code=303)

    email = _normalize_email_or_generate(db, email, name)
    existing = db.query(User).filter(User.email == email, User.id != user_id).first()
    if existing:
        return RedirectResponse(url=f"/vendedores/editar/{user_id}?erro=Email%20ja%20cadastrado", status_code=303)

    user.name = name
    user.email = email
    user.role = role or "seller"
    user.active = active == "1"
    if password:
        user.password_hash = hash_password(password)
    db.commit()

    _set_user_companies(db, user.id, _company_ids_from_form(company_ids))
    return RedirectResponse(url="/vendedores", status_code=303)
