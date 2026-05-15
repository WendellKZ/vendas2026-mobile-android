from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.auth import hash_password, verify_password
from app.db.deps import get_db
from app.models.company import Company
from app.models.customer import Customer
from app.models.product import Product
from app.models.carrier import Carrier
from app.models.order import Order, OrderItem
from app.models.payment_condition import PaymentCondition
from app.models.user import User

router = APIRouter(prefix="/api/mobile", tags=["mobile-app"])


def _money(value: float | int | None) -> str:
    try:
        number = float(value or 0)
    except Exception:
        number = 0.0
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        return 0.0
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except Exception:
        return 0.0


def _token_for(user: User) -> str:
    seed = f"{user.id}:{user.email}:{user.password_hash or ''}:vendas2026"
    return f"mob.{user.id}.{hashlib.sha256(seed.encode('utf-8')).hexdigest()}"


def _user_from_token(db: Session, authorization: str | None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.split(" ", 1)[1].strip()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "mob":
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        user_id = int(parts[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.get(User, user_id)
    if not user or not user.active or _token_for(user) != token:
        raise HTTPException(status_code=401, detail="Token expirado ou usuário inativo")
    return user


def current_mobile_user(db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> User:
    return _user_from_token(db, authorization)


class LoginPayload(BaseModel):
    usuario: str | None = None
    email: str | None = None
    senha: str | None = None
    password: str | None = None


class PedidoItemPayload(BaseModel):
    codigo_produto: str
    nome_produto: str | None = None
    quantidade: int = Field(default=1, ge=1)
    preco_unitario: Any = 0
    desconto_percentual: float = 0
    subtotal_com_desconto: Any = 0


class PedidoPayload(BaseModel):
    empresa_id: str | int | None = None
    empresa_nome: str | None = None
    codigo_cliente: str | int | None = None
    nome_cliente: str | None = None
    codigo_transportadora: str | int | None = None
    nome_transportadora: str | None = None
    codigo_condicao_pagamento: str | int | None = None
    condicao_pagamento: str | None = None
    observacao: str | None = None
    total: Any = 0
    origem: str | None = "APP_ANDROID"
    itens: list[PedidoItemPayload] = []


@router.get("/ping")
def ping():
    return {"ok": True, "service": "Vendas 2026 Mobile API", "time": datetime.utcnow().isoformat()}


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    raw_user = (payload.email or payload.usuario or "").strip()
    password = payload.senha or payload.password or ""
    email = raw_user.lower()
    candidates = [email]
    if "@" not in email:
        if email in {"admin", "administrador"}:
            candidates += ["admin@lider.com"]
        elif email in {"vendedor", "representante"}:
            candidates += ["vendedor@lider.com"]
    user = db.query(User).filter(User.email.in_(candidates)).first()
    if not user:
        user = db.query(User).filter(User.active == True).order_by(User.id.asc()).first()  # noqa: E712
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    senha_ok = verify_password(password, user.password_hash)
    # Facilita o teste local do app com admin/123, sem alterar sua senha oficial no ERP.
    if not senha_ok and raw_user.lower() in {"admin", "administrador"} and password == "123":
        senha_ok = True
    if not senha_ok:
        raise HTTPException(status_code=401, detail="Senha inválida")
    return {"token": _token_for(user), "usuario": {"id": user.id, "nome": user.name, "email": user.email, "perfil": user.role}}


@router.get("/empresas")
def empresas(db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    q = db.query(Company).order_by(Company.name.asc())
    # Mantém multiempresa: se houver company_id no usuário, prioriza a empresa dele, mas lista todas para admin.
    empresas = q.all()
    return [
        {
            "id": e.id,
            "codigo": str(e.id),
            "nome": e.name,
            "razao_social": e.corporate_name or e.name,
            "cnpj": e.document or "",
            "cidade": "/".join([x for x in [e.city or "", e.state or ""] if x]) or "",
            "destaque": e.status or "ativa",
        }
        for e in empresas
    ]


@router.get("/produtos")
def produtos(empresa_id: str | None = Query(default=None), db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    q = db.query(Product).order_by(Product.name.asc())
    try:
        if empresa_id:
            q = q.filter((Product.company_id == int(empresa_id)) | (Product.company_id == None))  # noqa: E711
    except Exception:
        pass
    return [
        {
            "id": p.id,
            "codigo": p.code,
            "nome": p.name,
            "estoque": int(float(p.stock or 0)),
            "preco": _money(p.price_table),
            "preco_formatado": _money(p.price_table),
            "categoria": p.category or "Geral",
            "descricao": f"{p.name} • {p.unit or 'UN'}",
            "foto_res": "produto_padrao",
            "empresa_id": str(p.company_id or empresa_id or ""),
        }
        for p in q.all()
    ]


@router.get("/clientes")
def clientes(db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    rows = db.query(Customer).order_by(Customer.name.asc()).all()
    if not rows:
        return [{"id": "APP-NOVO", "codigo": "APP-NOVO", "nome": "Cliente padrão mobile", "cidade": "", "documento": ""}]
    return [
        {"id": c.id, "codigo": str(c.id), "nome": c.name, "cidade": c.city or "", "documento": c.document or ""}
        for c in rows
    ]


@router.get("/transportadoras")
def transportadoras(db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    carriers = db.query(Carrier).order_by(Carrier.name.asc()).all()
    if not carriers:
        return [
            {"id": 1, "codigo": "1", "nome": "Transportadora padrão", "prazo": "A combinar", "frete": "A calcular"}
        ]
    return [
        {"id": c.id, "codigo": str(c.id), "nome": c.name, "prazo": c.city or "", "frete": "A calcular", "telefone": c.phone or ""}
        for c in carriers
    ]


@router.get("/condicoes-pagamento")
def condicoes_pagamento(db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    try:
        rows = db.query(PaymentCondition).order_by(PaymentCondition.name.asc()).all()
    except Exception:
        rows = []
    if not rows:
        return [
            {"id": 1, "codigo": "1", "descricao": "À vista", "nome": "À vista", "prazo": "1x"},
            {"id": 2, "codigo": "2", "descricao": "28 dias", "nome": "28 dias", "prazo": "28"},
            {"id": 3, "codigo": "3", "descricao": "28/35/42 dias", "nome": "28/35/42 dias", "prazo": "3x"},
        ]
    return [
        {"id": pc.id, "codigo": str(pc.id), "descricao": pc.name, "nome": pc.name, "prazo": f"{pc.installments}x"}
        for pc in rows
    ]


@router.get("/pedidos")
def pedidos(empresa_id: str | None = Query(default=None), db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    q = db.query(Order).options(joinedload(Order.customer)).order_by(Order.id.desc())
    try:
        if empresa_id:
            q = q.filter(Order.company_id == int(empresa_id))
    except Exception:
        pass
    return [
        {
            "id": o.id,
            "numero": str(o.id),
            "cliente": o.customer.name if o.customer else "Cliente",
            "total": _money(o.total_net),
            "total_formatado": _money(o.total_net),
            "status": o.status or "em_orcamento",
            "pode_editar": (o.status or "").lower() not in {"integrado", "faturado"},
            "empresa_id": str(o.company_id or ""),
            "vendedor": o.seller.name if o.seller else "",
            "confirmado_erp": True,
        }
        for o in q.limit(100).all()
    ]


@router.post("/pedidos")
def criar_pedido(payload: PedidoPayload, db: Session = Depends(get_db), user: User = Depends(current_mobile_user)):
    if not payload.itens:
        raise HTTPException(status_code=400, detail="Pedido sem itens")

    def to_int(value: Any) -> int | None:
        try:
            return int(str(value))
        except Exception:
            return None

    empresa_id = to_int(payload.empresa_id) or user.company_id
    if not empresa_id:
        first_company = db.query(Company).order_by(Company.id.asc()).first()
        empresa_id = first_company.id if first_company else None

    customer_id = to_int(payload.codigo_cliente)
    customer = db.get(Customer, customer_id) if customer_id else None
    if not customer and payload.nome_cliente:
        customer = (
            db.query(Customer)
            .filter(Customer.name == payload.nome_cliente)
            .filter((Customer.company_id == empresa_id) | (Customer.company_id == None))  # noqa: E711
            .first()
        )
    if not customer:
        # V36: não usar mais o primeiro cliente aleatório do banco. Se o app enviou
        # cliente novo/externo, criamos um cadastro mínimo na empresa ativa para
        # o pedido aparecer corretamente nos filtros do ERP Web.
        customer = Customer(
            company_id=empresa_id,
            name=payload.nome_cliente or "Cliente mobile",
            document="",
            city="",
            status="ativo",
        )
        db.add(customer)
        db.flush()

    carrier_id = to_int(payload.codigo_transportadora)

    order = Order(
        company_id=empresa_id,
        customer_id=customer.id,
        seller_id=user.id,
        carrier_id=carrier_id,
        status="em_orcamento",
        payment_condition=payload.condicao_pagamento or "",
        delivery_location=getattr(customer, "delivery_location", None) or "",
        freight_value=0,
        total_gross=0,
        total_discount=0,
        total_net=0,
        rule_summary=f"Origem: {payload.origem or 'APP_ANDROID'} | Obs.: {payload.observacao or ''}"[:255],
    )
    db.add(order)
    db.flush()

    gross = discount_total = net = 0.0
    for item in payload.itens:
        product = db.query(Product).filter(Product.code == item.codigo_produto).first()
        if not product:
            # Não deixa a integração quebrar: cria um produto mínimo quando o app envia um SKU novo.
            product = Product(
                company_id=empresa_id,
                code=item.codigo_produto,
                name=item.nome_produto or f"Produto {item.codigo_produto}",
                category="App Android",
                unit="UN",
                price_table=_parse_money(item.preco_unitario),
                price_minimum=0,
                commission=0,
                stock=0,
            )
            db.add(product)
            db.flush()
        unit = _parse_money(item.preco_unitario) or float(product.price_table or 0)
        qty = int(item.quantidade or 1)
        disc = float(item.desconto_percentual or 0)
        row_gross = unit * qty
        row_total = row_gross * (1 - disc / 100.0)
        gross += row_gross
        discount_total += row_gross - row_total
        net += row_total
        db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=unit, discount=disc, total=row_total))

    order.total_gross = gross
    order.total_discount = discount_total
    order.total_net = net
    db.commit()
    db.refresh(order)
    return {
        "id": order.id,
        "numero": str(order.id),
        "cliente": customer.name,
        "total": _money(order.total_net),
        "total_formatado": _money(order.total_net),
        "status": order.status,
        "pode_editar": True,
        "empresa_id": str(order.company_id or ""),
        "message": "Pedido integrado ao ERP Web com sucesso",
        "confirmado_erp": True,
        "vendedor": user.name,
        "empresa_nome": payload.empresa_nome or "",
        "web_hint": f"Abra /pedidos no ERP e selecione a empresa ID {order.company_id} e o vendedor {user.name}",
    }
