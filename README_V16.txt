ERP Vendas Pro - V16

Resumo da V16:
- Catálogo/produtos separados por empresa ativa.
- Pedidos separados por empresa ativa.
- Clientes compartilhados entre empresas.
- Transportadoras compartilhadas entre empresas.
- Troca rápida de empresa no topo.
- Login de vendedor com mais de uma empresa cai em Selecionar empresa.
- Novos produtos são vinculados à empresa ativa.
- Novos pedidos são vinculados à empresa ativa.
- Tela mantém o visual premium igual ao padrão original do Git.

Como rodar:
py -3.12 -m uvicorn app.main:app --reload --port 5098

Login admin:
admin@lider.com
admin123

Validação recomendada:
1. Faça login.
2. Escolha uma empresa.
3. Entre em Catálogo e cadastre um produto.
4. Troque de empresa no topo.
5. Veja que o produto não aparece na outra empresa.
6. Entre em Clientes e Transportadoras.
7. Veja que esses cadastros continuam compartilhados.
