from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.customer import Customer
from app.auth import current_user_from_cookie, is_admin
from app.services.company_context_service import company_context, require_active_company_or_redirect
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.cnpj_lookup_service import lookup_cnpj_data

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])
web_router = APIRouter()


def _only_digits(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def _duplicated_document(db: Session, document: str, ignore_id: int | None = None) -> bool:
    digits = _only_digits(document)
    if not digits:
        return False
    for customer_id, saved_document in db.query(Customer.id, Customer.document).all():
        if ignore_id is not None and customer_id == ignore_id:
            continue
        if _only_digits(saved_document) == digits:
            return True
    return False


@router.get("/lookup-cnpj/{cnpj}")
def lookup_cnpj(cnpj: str):
    digits = _only_digits(cnpj)
    if len(digits) != 14:
        raise HTTPException(status_code=400, detail="CNPJ inválido")

    result = lookup_cnpj_data(digits)
    return result.as_dict()


@router.get("/", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.id.desc()).all()


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    if _duplicated_document(db, payload.document):
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    obj = Customer(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@web_router.get("/clientes")
def clientes_page(request: Request, db: Session = Depends(get_db)):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    customers = db.query(Customer).order_by(Customer.id.desc()).all()
    existing_documents = [_only_digits(c.document) for c in customers if _only_digits(c.document)]
    erro = request.query_params.get("erro")
    return request.app.state.templates.TemplateResponse(
        "clientes.html",
        {"request": request, "customers": customers, "existing_documents": existing_documents, "erro": erro, "current_user": current_user, "active_seller": current_user, "is_admin": is_admin(current_user), **company_context(request, db, current_user)},
    )


@web_router.post("/clientes")
def clientes_create(
    request: Request,
    name: str = Form(...),
    corporate_name: str = Form(""),
    document: str = Form(""),
    state_registration: str = Form(""),
    city: str = Form(""),
    delivery_location: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    billing_email: str = Form(""),
    status: str = Form("ativo"),
    suframa: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    if _duplicated_document(db, document):
        return RedirectResponse(url="/clientes?erro=CNPJ%20ja%20cadastrado.%20Abra%20o%20cliente%20existente%20ou%20edite%20o%20cadastro.", status_code=303)

    suframa = (suframa or "").strip()
    modo = "automatico" if suframa else None
    fonte = "consulta_api" if suframa else None
    status_suframa = "ativo" if suframa else None
    consultado_em = datetime.utcnow() if suframa else None

    obj = Customer(
        # V16: cliente é cadastro compartilhado entre empresas.
        company_id=None,
        name=name,
        corporate_name=corporate_name or None,
        document=document or None,
        state_registration=state_registration or None,
        city=city or None,
        delivery_location=delivery_location or None,
        email=email or None,
        phone=phone or None,
        billing_email=billing_email or None,
        status=status,
        suframa=suframa or None,
        suframa_status=status_suframa,
        suframa_fonte=fonte,
        suframa_consultado_em=consultado_em,
        suframa_modo=modo,
    )
    db.add(obj)
    db.commit()
    return RedirectResponse(url="/clientes", status_code=303)


@web_router.get("/clientes/editar/{customer_id}")
def clientes_edit_page(customer_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return request.app.state.templates.TemplateResponse(
        "cliente_editar.html",
        {"request": request, "customer": customer, "current_user": current_user, "active_seller": current_user, "is_admin": is_admin(current_user), **company_context(request, db, current_user)},
    )


@web_router.post("/clientes/editar/{customer_id}")
def clientes_edit_save(
    customer_id: int,
    request: Request,
    name: str = Form(...),
    corporate_name: str = Form(""),
    document: str = Form(""),
    state_registration: str = Form(""),
    city: str = Form(""),
    delivery_location: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    billing_email: str = Form(""),
    status: str = Form("ativo"),
    suframa: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if _duplicated_document(db, document, ignore_id=customer_id):
        return RedirectResponse(url="/clientes?erro=CNPJ%20ja%20cadastrado%20em%20outro%20cliente.", status_code=303)

    customer.name = name
    customer.corporate_name = corporate_name or None
    customer.document = document or None
    customer.state_registration = state_registration or None
    customer.city = city or None
    customer.delivery_location = delivery_location or None
    customer.email = email or None
    customer.phone = phone or None
    customer.billing_email = billing_email or None
    suframa = (suframa or "").strip()
    customer.status = status
    customer.suframa = suframa or None
    if suframa:
        customer.suframa_status = "ativo"
        customer.suframa_fonte = "consulta_api"
        customer.suframa_consultado_em = datetime.utcnow()
        customer.suframa_modo = "automatico"
    else:
        customer.suframa_status = None
        customer.suframa_fonte = None
        customer.suframa_consultado_em = None
        customer.suframa_modo = None
    db.commit()

    return RedirectResponse(url="/clientes", status_code=303)
