# V-PRO 8.4 — Consulta CNPJ/SUFRAMA + Desconto unitário no assistente

## Ajustes incluídos

- Cadastro de cliente agora consulta o backend `/api/v1/customers/lookup-cnpj/{cnpj}`.
- O backend consulta a BrasilAPI para dados cadastrais.
- O backend permite configurar uma API externa/comercial para SUFRAMA via `.env`:
  - `SUFRAMA_API_URL=https://sua-api.com.br/cnpj/{cnpj}`
  - `SUFRAMA_API_TOKEN=seu_token`
- Mantido fallback local apenas para testes quando a API externa não estiver configurada.
- Assistente de Pedido agora mostra o desconto por unidade em cada item do carrinho.
- Conferência do pedido também mostra desconto unitário por item.

## Observação sobre SUFRAMA

APIs públicas gratuitas de CNPJ normalmente retornam dados cadastrais da Receita, mas nem sempre retornam SUFRAMA. Por isso o sistema ficou preparado para plugar uma API comercial/oficial de SUFRAMA sem mexer no front.
