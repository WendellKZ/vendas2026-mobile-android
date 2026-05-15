"""
Patch opcional FastAPI - V38 Configuração Remota Mobile

Como usar no ERP:
1. Copie este arquivo para uma pasta do ERP, por exemplo app/mobile_config_v38.py
2. No app/main.py, importe e inclua o router:
   from app.mobile_config_v38 import router as mobile_config_router
   app.include_router(mobile_config_router)

Depois teste:
https://SEU-ERP.onrender.com/api/mobile/config
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/mobile", tags=["mobile-config"])


@router.get("/config")
def mobile_config():
    return {
        "app_version_label": "V38",
        "mensagem_home": "",
        "cor_primaria": "#2563EB",
        "mostrar_notificacoes": True,
        "mostrar_rota": True,
        "mostrar_historico": True,
        "mostrar_campanhas": True,
        "mostrar_offline": True,
        "mostrar_empresa": True,
        "label_novo_pedido": "Novo pedido",
        "label_pedidos": "Pedidos",
        "label_produtos": "Produtos",
        "label_clientes": "Clientes",
        "label_novo_cliente": "Novo cliente",
        "label_transportadora": "Transportadora",
    }
