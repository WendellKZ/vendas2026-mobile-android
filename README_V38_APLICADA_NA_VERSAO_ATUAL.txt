V38 aplicada sobre a versão atual enviada pelo usuário.

Incluído:
- Offline > Sincronizar agora busca /api/mobile/config no ERP.
- Possibilidade de ocultar/exibir cards simples pelo retorno do ERP.
- Possibilidade de alterar nomes dos menus pelo retorno do ERP.
- Mantidas as correções da versão atual enviada.

Endpoint esperado no ERP:
GET /api/mobile/config

Exemplo de retorno:
{
  "config": {
    "app_version_label": "V38",
    "mensagem_home": "Aviso comercial opcional",
    "mostrar_notificacoes": true,
    "mostrar_rota": true,
    "mostrar_historico": true,
    "mostrar_campanhas": true,
    "mostrar_offline": true,
    "mostrar_empresa": true,
    "label_novo_pedido": "Novo pedido",
    "label_pedidos": "Pedidos",
    "label_produtos": "Produtos",
    "label_clientes": "Clientes",
    "label_novo_cliente": "Novo cliente",
    "label_transportadora": "Transportadora"
  }
}

Observação: a compilação no sandbox não foi concluída porque o Gradle tentou baixar dependências da internet, que não está disponível neste ambiente. No Android Studio, basta abrir o projeto, sincronizar e gerar o APK.
