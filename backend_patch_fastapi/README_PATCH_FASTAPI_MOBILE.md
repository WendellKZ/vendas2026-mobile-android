# Patch FastAPI - API Mobile Vendas 2026

Seu ERP Web roda com Uvicorn na porta 5098.

Comando recomendado:

```powershell
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --reload --port 5098
```

Endpoints esperados pelo app:

- POST `/api/mobile/login`
- GET `/api/mobile/empresas`
- GET `/api/mobile/produtos?empresa_id=1`
- GET `/api/mobile/pedidos?empresa_id=1`
- GET `/api/mobile/clientes`
- GET `/api/mobile/transportadoras`
- GET `/api/mobile/condicoes-pagamento`
- POST `/api/mobile/pedidos`

Se ainda não existirem no ERP Web, aplique rotas equivalentes no `app.main`.
