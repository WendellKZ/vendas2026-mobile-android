from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import current_user_from_cookie, is_admin
from app.db.deps import get_db
from app.services.company_context_service import (
    ACTIVE_COMPANY_COOKIE,
    company_context,
    get_allowed_companies,
    user_can_access_company,
)

web_router = APIRouter()


def _require_logged(request: Request, db: Session):
    user = current_user_from_cookie(request, db)
    if not user:
        return None
    return user


def _user_context(request: Request, db: Session, current_user):
    ctx = {
        "current_user": current_user,
        "active_seller": current_user,
        "is_admin": is_admin(current_user),
    }
    ctx.update(company_context(request, db, current_user))
    return ctx


@web_router.get("/selecionar-empresa")
def selecionar_empresa_page(request: Request, db: Session = Depends(get_db)):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    companies = get_allowed_companies(db, current_user)

    if len(companies) == 1:
        response = RedirectResponse(url="/painel", status_code=303)
        response.set_cookie(ACTIVE_COMPANY_COOKIE, str(companies[0].id), max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
        return response

    return request.app.state.templates.TemplateResponse(
        "selecionar_empresa.html",
        {
            "request": request,
            "companies": companies,
            "title": "Selecionar empresa",
            "subtitle": "Escolha por qual empresa você deseja operar neste acesso.",
            **_user_context(request, db, current_user),
        },
    )


@web_router.post("/selecionar-empresa")
def selecionar_empresa_save(
    request: Request,
    company_id: int = Form(...),
    db: Session = Depends(get_db),
):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    if not user_can_access_company(db, current_user, company_id):
        return RedirectResponse(url="/selecionar-empresa?erro=empresa_nao_autorizada", status_code=303)

    response = RedirectResponse(url="/painel", status_code=303)
    response.set_cookie(ACTIVE_COMPANY_COOKIE, str(company_id), max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
    return response


@web_router.post("/trocar-empresa")
def trocar_empresa(
    request: Request,
    company_id: int = Form(...),
    db: Session = Depends(get_db),
):
    current_user = _require_logged(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    if not user_can_access_company(db, current_user, company_id):
        return RedirectResponse(url="/selecionar-empresa?erro=empresa_nao_autorizada", status_code=303)

    referer = request.headers.get("referer") or "/painel"
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie(ACTIVE_COMPANY_COOKIE, str(company_id), max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
    return response
