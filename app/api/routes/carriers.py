from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.carrier import Carrier
from app.auth import current_user_from_cookie, is_admin
from app.services.company_context_service import company_context, require_active_company_or_redirect
from app.schemas.carrier import CarrierCreate, CarrierRead

router = APIRouter(prefix="/api/v1/carriers", tags=["carriers"])
web_router = APIRouter()


@router.get("/", response_model=list[CarrierRead])
def list_carriers(db: Session = Depends(get_db)):
    return db.query(Carrier).order_by(Carrier.id.desc()).all()


@router.post("/", response_model=CarrierRead, status_code=201)
def create_carrier(payload: CarrierCreate, db: Session = Depends(get_db)):
    obj = Carrier(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@web_router.get("/transportadoras")
def carriers_page(request: Request, db: Session = Depends(get_db)):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    carriers = db.query(Carrier).order_by(Carrier.id.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "transportadoras.html",
        {"request": request, "carriers": carriers, "current_user": current_user, "active_seller": current_user, "is_admin": is_admin(current_user), **company_context(request, db, current_user)},
    )


@web_router.post("/transportadoras")
def carriers_create(
    request: Request,
    name: str = Form(...),
    document: str = Form(""),
    city: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    obj = Carrier(
        # V16: transportadora é cadastro compartilhado entre empresas.
        company_id=None,
        name=name,
        document=document or None,
        city=city or None,
        phone=phone or None,
        email=email or None,
    )
    db.add(obj)
    db.commit()
    return RedirectResponse(url="/transportadoras", status_code=303)


@web_router.get("/transportadoras/editar/{carrier_id}")
def carriers_edit_page(carrier_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    carrier = db.get(Carrier, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Transportadora não encontrada")
    return request.app.state.templates.TemplateResponse(
        "transportadora_editar.html",
        {"request": request, "carrier": carrier, "current_user": current_user, "active_seller": current_user, "is_admin": is_admin(current_user), **company_context(request, db, current_user)},
    )


@web_router.post("/transportadoras/editar/{carrier_id}")
def carriers_edit_save(
    carrier_id: int,
    request: Request,
    name: str = Form(...),
    document: str = Form(""),
    city: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = current_user_from_cookie(request, db)
    active_company = require_active_company_or_redirect(request, db, current_user)
    if isinstance(active_company, RedirectResponse):
        return active_company
    carrier = db.get(Carrier, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Transportadora não encontrada")

    carrier.name = name
    carrier.document = document or None
    carrier.city = city or None
    carrier.phone = phone or None
    carrier.email = email or None
    db.commit()

    return RedirectResponse(url="/transportadoras", status_code=303)
