# V16.4 - Correção menu + agente

Inclui:

- Ícones SVG no menu lateral
- Correção do visual dos ícones
- Botão flutuante do Agente de Pedidos
- Painel rápido com atalhos:
  - Criar pedido guiado
  - Consultar cliente
  - Ver catálogo

## Aplicação

Copie as pastas `templates`, `static` e `scripts` para `C:\erp_vendas_completo`.

Depois rode:

```powershell
cd C:\erp_vendas_completo
python .\scripts\aplicar_v16_4_css.py
docker compose down
docker compose up -d --build
```
