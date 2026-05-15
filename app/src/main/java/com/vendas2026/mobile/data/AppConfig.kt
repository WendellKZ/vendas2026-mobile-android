package com.vendas2026.mobile.data

object AppConfig {
    /**
     * V34 configurada para integração online com ERP Web no Render.
     *
     * EDITE AQUI a URL real do seu ERP publicado no Render.
     * Exemplo:
     * DEFAULT_API_BASE_URL = "https://vendas2026-erp.onrender.com"
     *
     * Importante:
     * - Não use 10.0.2.2 no APK instalado no celular.
     * - Não use porta 5098 quando o ERP estiver no Render.
     * - Deixe sem barra no final.
     */
    const val DEFAULT_API_BASE_URL = "https://erp-vendas-vpro.onrender.com"
    var API_BASE_URL = DEFAULT_API_BASE_URL
    const val MOCK_MODE = false

    const val ENDPOINT_LOGIN = "/api/mobile/login"
    const val ENDPOINT_PRODUTOS = "/api/mobile/produtos"
    const val ENDPOINT_PEDIDOS = "/api/mobile/pedidos"
    const val ENDPOINT_CLIENTES = "/api/mobile/clientes"
    const val ENDPOINT_TRANSPORTADORAS = "/api/mobile/transportadoras"
    const val ENDPOINT_CONDICOES_PAGAMENTO = "/api/mobile/condicoes-pagamento"
    const val ENDPOINT_CRIAR_PEDIDO = "/api/mobile/pedidos"
    const val ENDPOINT_CONFIG_MOBILE = "/api/mobile/config"
}
