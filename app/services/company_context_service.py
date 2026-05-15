from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User
from app.models.user_company import UserCompany

ACTIVE_COMPANY_COOKIE = "active_company_id"


def get_allowed_companies(db: Session, user: User | None) -> list[Company]:
    if not user:
        return []

    if user.role == "admin":
        return db.query(Company).order_by(Company.name).all()

    companies = (
        db.query(Company)
        .join(UserCompany, UserCompany.company_id == Company.id)
        .filter(UserCompany.user_id == user.id)
        .order_by(Company.name)
        .all()
    )

    # Compatibilidade com usuários antigos que ainda tinham company_id direto.
    if not companies and getattr(user, "company_id", None):
        company = db.get(Company, user.company_id)
        if company:
            companies = [company]
    return companies


def get_active_company_id_from_request(request: Request) -> int | None:
    raw = request.cookies.get(ACTIVE_COMPANY_COOKIE)
    try:
        return int(raw) if raw else None
    except (TypeError, ValueError):
        return None


def get_active_company(request: Request, db: Session, user: User | None) -> Company | None:
    allowed = get_allowed_companies(db, user)
    if not allowed:
        return None

    active_id = get_active_company_id_from_request(request)
    for company in allowed:
        if company.id == active_id:
            return company

    # Admin pode escolher. Vendedor com uma única empresa entra direto nela.
    return allowed[0] if len(allowed) == 1 else None


def get_active_company_id(request: Request, db: Session, user: User | None) -> int | None:
    company = get_active_company(request, db, user)
    return company.id if company else None


def user_can_access_company(db: Session, user: User | None, company_id: int) -> bool:
    if not user:
        return False
    if user.role == "admin":
        return db.query(Company).filter(Company.id == company_id).first() is not None
    return (
        db.query(UserCompany)
        .filter(UserCompany.user_id == user.id, UserCompany.company_id == company_id)
        .first()
        is not None
    ) or getattr(user, "company_id", None) == company_id


def company_context(request: Request, db: Session, user: User | None) -> dict:
    allowed = get_allowed_companies(db, user)
    active = get_active_company(request, db, user)
    return {
        "allowed_companies": allowed,
        "active_company": active,
        "active_company_id": active.id if active else None,
    }


def require_active_company_or_redirect(request: Request, db: Session, user: User | None):
    allowed = get_allowed_companies(db, user)
    if not allowed:
        return RedirectResponse(url="/empresas", status_code=303) if user and user.role == "admin" else RedirectResponse(url="/login", status_code=303)
    active = get_active_company(request, db, user)
    if not active:
        return RedirectResponse(url="/selecionar-empresa", status_code=303)
    return active


def with_company_filter(query, model, company_id: int | None):
    if company_id is None or not hasattr(model, "company_id"):
        return query
    return query.filter(model.company_id == company_id)


def ensure_default_company_links(db: Session) -> None:
    """Garante versão testável mesmo com banco antigo: cria vínculos e preenche dados antigos."""
    companies = db.query(Company).order_by(Company.id).all()
    if not companies:
        companies = [
            Company(name="BRIDI NETWORK", corporate_name="BRIDI NETWORK PRODUCOES LTDA", document="15.803.398/0001-71", status="ativa"),
            Company(name="Líder Brinquedos", corporate_name="LIDER INDUSTRIA E COMERCIO DE BRINQUEDOS LTDA", document="59.400.853/0001-63", status="ativa"),
        ]
        db.add_all(companies)
        db.commit()
        for c in companies:
            db.refresh(c)

    users = db.query(User).all()
    for user in users:
        existing_links = {
            link.company_id
            for link in db.query(UserCompany).filter(UserCompany.user_id == user.id).all()
        }

        # Admin e usuários João ficam com acesso a todas as empresas para validar a V15 multiempresa.
        user_key = f"{user.name or ''} {user.email or ''}".lower()
        should_have_all = user.role == "admin" or "joao" in user_key or "joão" in user_key

        if should_have_all:
            for company in companies:
                if company.id not in existing_links:
                    db.add(UserCompany(user_id=user.id, company_id=company.id))
            continue

        if not existing_links:
            company_id = getattr(user, "company_id", None) or companies[0].id
            db.add(UserCompany(user_id=user.id, company_id=company_id))
    db.commit()

    first_id = companies[0].id
    # V16: pedidos e produtos são separados por empresa; clientes e transportadoras ficam compartilhados.
    for table in ["products", "orders"]:
        try:
            db.execute(text(f"UPDATE {table} SET company_id = :cid WHERE company_id IS NULL"), {"cid": first_id})
        except Exception:
            pass

    # V16: remove amarração antiga de clientes/transportadoras para aparecerem em todas as empresas.
    for table in ["customers", "carriers"]:
        try:
            db.execute(text(f"UPDATE {table} SET company_id = NULL"))
        except Exception:
            pass
    db.commit()

    # Cria um item de catálogo por empresa vazia para o teste ficar claro no primeiro acesso.
    try:
        from app.models.product import Product
        for company in companies:
            count = db.query(Product).filter(Product.company_id == company.id).count()
            if count == 0:
                code = f"V16-{company.id:03d}"
                db.add(Product(
                    company_id=company.id,
                    code=code,
                    name=f"Produto exclusivo {company.name}",
                    category="Catálogo empresa",
                    unit="UN",
                    price_table=99.90 + company.id,
                    price_minimum=79.90 + company.id,
                    commission=5,
                    stock=50,
                ))
        db.commit()
    except Exception:
        db.rollback()
