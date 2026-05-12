package com.vendas2026.mobile.data

object AppConfig {
    /**
     * V26 vem preparada para integrar com o ERP Web por API.
     * Para gravar pedido no sistema Web:
     * 1) aplique o patch Flask da pasta backend_patch_flask no ERP;
     * 2) rode o ERP localmente;
     * 3) mantenha MOCK_MODE=false para enviar pedidos ao ERP Web.
     *
     * Emulador Android acessando backend local no PC:
     * API_BASE_URL = "http://10.0.2.2:5098"
     *
     * Celular físico acessando backend local:
     * use o IP do PC na rede, exemplo "http://192.168.0.50:5098"
     */
    const val API_BASE_URL = "http://10.0.2.2:5098"
    const val MOCK_MODE = false

    const val ENDPOINT_LOGIN = "/api/mobile/login"
    const val ENDPOINT_PRODUTOS = "/api/mobile/produtos"
    const val ENDPOINT_PEDIDOS = "/api/mobile/pedidos"
    const val ENDPOINT_CLIENTES = "/api/mobile/clientes"
    const val ENDPOINT_TRANSPORTADORAS = "/api/mobile/transportadoras"
    const val ENDPOINT_CONDICOES_PAGAMENTO = "/api/mobile/condicoes-pagamento"
    const val ENDPOINT_CRIAR_PEDIDO = "/api/mobile/pedidos"
}
