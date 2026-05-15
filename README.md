# ERP Vendas Completo

Projeto FastAPI com painel visual, cadastro de clientes, produtos e pedidos.

## Portas
- API e painel: `5098`
- PostgreSQL: `5434`

## Subir com Docker
```powershell
docker compose down
docker compose up -d --build
```

## Popular dados iniciais
```powershell
docker compose exec api sh -lc "PYTHONPATH=/app python scripts/seed.py"
```

## Acessos
- Swagger: `http://localhost:5098/docs`
- Painel: `http://localhost:5098/painel`
- Pedidos: `http://localhost:5098/pedidos`
- Clientes: `http://localhost:5098/clientes`
- Produtos: `http://localhost:5098/produtos`

## Observação
Este pacote foi preparado para ser copiado por cima da pasta oficial do projeto:
`C:\erp_vendas_completo`


## V-PRO Front Profissional

Esta versão inclui uma evolução completa do front comercial:

- Dashboard premium com atalhos rápidos e cards de indicadores.
- Menu lateral escuro, moderno e fixo.
- Tela de pedidos em formato pipeline/lista profissional.
- Fluxo de novo pedido com carrinho comercial, cálculo em tempo real e alerta de desconto alto.
- Catálogo de produtos com cards visuais e lista operacional.
- Rotas web de edição e integração de pedidos corrigidas.

### Rodar localmente

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Acesse: http://127.0.0.1:8000/painel


## Correção V-PRO 2.1

Esta versão corrige a tela vazia/erro ao abrir `localhost:5098`:

- Inicialização do banco com tentativas automáticas para Docker/PostgreSQL.
- Correção de compatibilidade com bancos antigos que ainda não tinham colunas novas.
- Caminhos de `templates` e `static` robustos, independente da pasta onde o comando for executado.
- Correção de rota duplicada em `/pedidos`.

### Passo 2 — Aplicar
Extraia este zip e substitua a pasta do projeto anterior.

### Passo 3 — Rodar com Docker
Dê dois cliques em `iniciar_docker.bat` ou rode:

```powershell
docker compose down
docker compose up --build
```

Acesse: `http://localhost:5098/painel`

### Passo 4 — Rodar local sem Docker
Dê dois cliques em `iniciar_local_5098.bat` ou rode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 5098
```

### Passo 5 — Validar
Abra:

- `http://localhost:5098/health`
- `http://localhost:5098/painel`
- `http://localhost:5098/pedidos`
