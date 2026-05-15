V35 - Ajustes de Pedidos e SUFRAMA

Alterações:
1. Tela Pedidos:
   - Removido o botão Novo Pedido duplicado quando não há pedidos encontrados.
   - Mantido apenas o card com ação Novo Pedido e o botão Voltar ao menu.

2. Cadastro de Novo Cliente por CNPJ:
   - Melhorada a leitura de SUFRAMA sem quebrar as APIs existentes.
   - Continua usando CNPJ.ws primeiro e BrasilAPI como fallback.
   - Agora tenta encontrar SUFRAMA em campos simples e também em arrays como inscricoes_suframa.
   - Campos continuam editáveis caso a API pública não retorne SUFRAMA.

3. Nenhuma integração existente foi removida.

Antes de gerar o APK:
- Confira a URL do Render em:
  app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt

Depois:
- Android Studio > Sync Project with Gradle Files
- Build > Build Bundle(s) / APK(s) > Build APK(s)
