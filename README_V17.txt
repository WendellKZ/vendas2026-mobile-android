ERP Vendas Pro - V17

Evoluções aplicadas:
- Estoque real por empresa ativa.
- Catálogo, preço de tabela e preço mínimo separados por empresa.
- Bloqueio no front para impedir inserir quantidade acima do estoque disponível.
- Validação no backend antes de integrar pedido.
- Baixa automática do estoque ao integrar pedido.
- Reposição automática do estoque caso um pedido integrado seja cancelado.
- Dashboard com ticket médio, valor de estoque, produtos zerados e baixo estoque.
- Painel de alertas inteligentes V17.
- Cadastro rápido de produto já vinculado à empresa ativa.
- Clientes e transportadoras seguem compartilhados entre empresas.

Como rodar:
py -3.12 -m uvicorn app.main:app --reload --port 5098

Login padrão:
admin@lider.com
admin123
