ERP Vendas Completo - V-PRO 3.1 corrigida

Correções principais:
- inicialização local usa SQLite por padrão, evitando erro de PostgreSQL/db fora do Docker;
- auto-migration cria colunas novas em banco antigo;
- cria usuário admin padrão se não existir;
- cria vendedor padrão se não existir;
- mantém compatibilidade com Docker/PostgreSQL via docker-compose.

Acessos padrão:
Admin: admin@lider.com / admin123
Vendedor: vendedor@lider.com / 123456

Rodar local:
1. Extrair o ZIP.
2. Executar iniciar_local_5098.bat.
3. Acessar http://localhost:5098

Se usar Docker:
1. Executar iniciar_docker.bat.
2. Acessar http://localhost:5098
