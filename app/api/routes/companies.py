from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import current_user_from_cookie, is_admin
from app.db.deps import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead
from app.services.cnpj_lookup_service import lookup_cnpj_data, only_digits

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])
web_router = APIRouter()


def _company_value(company: Company, attr: str, default: str = ""):
    return getattr(company, attr, default) or default


def _duplicated_document(db: Session, document: str, ignore_id: int | None = None) -> bool:
    digits = only_digits(document)
    if not digits:
        return False
    for company_id, saved_document in db.query(Company.id, Company.document).all():
        if ignore_id is not None and company_id == ignore_id:
            continue
        if only_digits(saved_document) == digits:
            return True
    return False


def _user_context(request: Request, db: Session):
    current_user = current_user_from_cookie(request, db)
    return {
        "current_user": current_user,
        "active_seller": current_user,
        "is_admin": is_admin(current_user),
    }


@router.get("/", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.id).all()


@router.post("/", response_model=CompanyRead, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    obj = Company(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@web_router.get("/empresas")
def empresas_page(request: Request, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.id.desc()).all()
    erro = request.query_params.get("erro")
    return request.app.state.templates.TemplateResponse(
        "empresas.html",
        {
            "request": request,
            "companies": companies,
            "erro": erro,
            "title": "Empresas",
            "subtitle": "Base multiempresa do grupo: cadastre CNPJs, prepare catálogos e permissões por empresa.",
            **_user_context(request, db),
        },
    )


@web_router.post("/empresas")
def empresas_create(
    request: Request,
    name: str = Form(...),
    corporate_name: str = Form(""),
    document: str = Form(""),
    state_registration: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    suframa: str = Form(""),
    status: str = Form("ativa"),
    db: Session = Depends(get_db),
):
    if _duplicated_document(db, document):
        return RedirectResponse(url="/empresas?erro=CNPJ%20ja%20cadastrado%20em%20outra%20empresa.", status_code=303)

    company = Company(
        name=name,
        corporate_name=corporate_name or None,
        document=document or None,
        state_registration=state_registration or None,
        city=city or None,
        state=state or None,
        phone=phone or None,
        email=email or None,
        suframa=suframa or None,
        status=status or "ativa",
    )
    db.add(company)
    db.commit()
    return RedirectResponse(url="/empresas", status_code=303)


@web_router.get("/empresas/editar/{company_id}")
def empresas_edit_page(company_id: int, request: Request, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        return RedirectResponse(url="/empresas?erro=Empresa%20nao%20encontrada", status_code=303)
    return request.app.state.templates.TemplateResponse(
        "empresa_editar.html",
        {
            "request": request,
            "company": company,
            "title": f"Editar empresa #{company.id}",
            "subtitle": "Atualize dados comerciais e fiscais da empresa do grupo.",
            **_user_context(request, db),
        },
    )


@web_router.post("/empresas/editar/{company_id}")
def empresas_edit_save(
    company_id: int,
    request: Request,
    name: str = Form(...),
    corporate_name: str = Form(""),
    document: str = Form(""),
    state_registration: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    suframa: str = Form(""),
    status: str = Form("ativa"),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        return RedirectResponse(url="/empresas?erro=Empresa%20nao%20encontrada", status_code=303)
    if _duplicated_document(db, document, ignore_id=company_id):
        return RedirectResponse(url="/empresas?erro=CNPJ%20ja%20cadastrado%20em%20outra%20empresa.", status_code=303)

    company.name = name
    company.corporate_name = corporate_name or None
    company.document = document or None
    company.state_registration = state_registration or None
    company.city = city or None
    company.state = state or None
    company.phone = phone or None
    company.email = email or None
    company.suframa = suframa or None
    company.status = status or "ativa"
    db.commit()
    return RedirectResponse(url="/empresas", status_code=303)


@router.get("/lookup-cnpj/{cnpj}")
def lookup_company_cnpj(cnpj: str):
    return lookup_cnpj_data(cnpj).as_dict()
