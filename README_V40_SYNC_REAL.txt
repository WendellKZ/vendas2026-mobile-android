V40 — Sincronização REAL ERP ↔ Mobile

O que foi aplicado no app Android:
- Botão Offline > Sincronizar agora agora envia pedidos pendentes e recebe dados reais do ERP.
- Atualiza produtos, clientes, transportadoras, condições de pagamento e pedidos/status.
- Salva cache offline no aparelho usando SharedPreferences por empresa.
- Se o ERP/Render estiver indisponível, as telas usam o último cache sincronizado.
- Ao abrir Produtos/Clientes/Pedidos, o app tenta buscar do ERP e cai no cache offline se falhar.

Importante para o ERP Web:
O app consome estes endpoints:
- GET  /api/mobile/ping
- POST /api/mobile/login
- GET  /api/mobile/empresas
- GET  /api/mobile/produtos?empresa_id=ID
- GET  /api/mobile/clientes
- GET  /api/mobile/transportadoras
- GET  /api/mobile/condicoes-pagamento
- GET  /api/mobile/pedidos?empresa_id=ID
- POST /api/mobile/pedidos
- GET  /api/mobile/config

Incluí um patch opcional em:
backend_patch_fastapi/app/api/routes/mobile_compat.py

Se o seu ERP já tem app/api/routes/mobile_compat.py, substitua pelo arquivo do patch e confira se app/main.py possui:
from app.api.routes.mobile_compat import router as mobile_compat_router
app.include_router(mobile_compat_router)

Depois suba o ERP no GitHub/Render e gere o APK do app.
