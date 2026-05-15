V-PRO 6 - Assistente Inteligente Simulado

Novidades:
- IA simulada adaptativa sem custo de API.
- Campo de comando livre: cliente, pagamento, transportadora e produtos em uma frase.
- Reconhecimento de voz no navegador quando disponível.
- Aprendizado local por representante usando localStorage.
- Sugestões com base no histórico real de pedidos do vendedor.
- Preferência de pagamento e transportadora por vendedor.

Como testar:
1. Extraia o projeto.
2. Execute iniciar_local_5098.bat.
3. Acesse http://localhost:5098.
4. Entre com admin@lider.com / admin123 ou vendedor@lider.com / 123456.
5. Abra Assistente de Pedido.
6. Teste um comando como:
   cliente Loja Sol, pagamento 28 dias, transportadora Jaja, 10 do produto carrinho

Observação:
Esta versão não usa OpenAI nem API paga. O aprendizado fica salvo no navegador do representante e também usa o histórico do banco para sugerir padrões.
