# V-PRO 8.5 - Assistente com orçamento + datas nos pedidos

## Alterações

- Assistente de Pedido agora possui opção **Manter como orçamento**.
- Botão **Enviar pedido para conferência** mantém o fluxo normal com regras comerciais/aprovação.
- Tela de Pedidos agora exibe data e hora em que o pedido foi digitado.
- Cada pedido mostra badge discreta: **Hoje**, **Ontem** ou data resumida.

## Como testar

1. Execute `iniciar_local_5098.bat`.
2. Acesse `http://localhost:5098/assistente-pedido`.
3. Monte um pedido e teste os dois botões finais:
   - Manter como orçamento
   - Enviar pedido para conferência
4. Acesse `http://localhost:5098/pedidos` e confira a data/hora no card.
